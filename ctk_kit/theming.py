"""运行时换色：把用户挑的颜色直接作用到**已经存在**的控件上。

``tokens`` 里的颜色是模块级常量，控件在构造时就把值取走了，所以改完令牌
界面不会自己变。这个模块补上中间那一层：

1. 改 ``tokens`` 的全局值（之后新建的控件自动用新色）；
2. 找到所有已存在的控件，把它们的颜色属性从「旧令牌值」换成「新令牌值」；
3. 让每个 CTk 控件重绘一遍，自绘控件（canvas / Pillow）调用登记过的回调。

用法::

    from ctk_kit import theming

    theming.apply_palette({"COLOR_ACTIVE": "#606269"})      # 改一个令牌
    theming.apply_palette({"COLOR_TEXT": "#e8eaed"})        # 改另一个
    theming.reset_palette()                                  # 全部还原

``tokens`` 现在只有一套毛玻璃配色，令牌就是 ``"#RRGGBB"`` 字符串。控件在
构造时把颜色取走存成字符串，所以这里按「旧色→新色」的替换表改属性：
只替换本次真正改过的令牌对应的颜色，不会把别的令牌的控件顺手改掉。

自绘控件（滑块、表格、树、日历这些自己画 canvas 的）没法靠换属性刷新，
用 :func:`register_redraw` 登记一个重绘函数，换色时会一并调用。
"""

from __future__ import annotations

import json
import tkinter as tk
import weakref
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Tuple

from . import tokens as T
from .theme import color_of

__all__ = [
    "apply_palette",
    "current_palette",
    "describe_usage",
    "find_usage",
    "load_palette",
    "palette_changes",
    "register_redraw",
    "refresh",
    "reset_palette",
    "save_palette",
    "set_darken",
    "usage_summary",
]

#: 一份调色板：``{令牌名: "#RRGGBB"}``。
Palette = Dict[str, str]

#: 当前覆盖掉的令牌：``{令牌名: "#RRGGBB"}``。重置时按它还原。
#: 这里存的是**用户挑的原色**，渲染时再按 :data:`_DARKEN` 压暗。
_OVERRIDES: Palette = {}

#: 自定义颜色整体的明度系数：毛玻璃主题下 0.8（暗 20%），其它主题 1.0。
_DARKEN: float = 1.0

#: 自绘控件的重绘回调：``{widget 路径: (弱引用, 回调)}``。
_REDRAW: Dict[str, Tuple[weakref.ref, Callable[[], Any]]] = {}


def _token_values() -> Palette:
    """``tokens`` 里所有 ``COLOR_`` 开头的颜色令牌。

    令牌都是字符串；调用方自己塞进来的色对按「最后一项」取值，和
    :func:`ctk_kit.theme.color_of` 保持一致。
    """
    values: Palette = {}
    for name, value in vars(T).items():
        if not name.startswith("COLOR_"):
            continue
        if isinstance(value, str):
            values[name] = value
        elif isinstance(value, (tuple, list)):
            parts = [str(part) for part in value if part]
            if parts:
                values[name] = parts[-1]
    return values


#: 导入时各令牌的原值，``reset_palette()`` 用它兜底。必须在这里就抓，
#: 惰性初始化会在第一次重置时拿到「已经被改过」的值。
_BASELINE: Palette = _token_values()


def _baseline() -> Palette:
    """导入时抓一次原值；之后 ``tokens`` 被改也还留着。"""
    return _BASELINE


def _normalized(value: Any) -> Optional[str]:
    """把用户给的单个颜色 / 色对统一成单色字符串。"""
    if isinstance(value, str):
        color = value.strip()
        return color or None
    if isinstance(value, (tuple, list)):
        parts = [str(part).strip() for part in value if part]
        return parts[-1] if parts else None
    return None


def _single_color(value: Any) -> str:
    """按当前外观把令牌取成单个颜色字符串（取不出来就返回空串）。"""
    try:
        return color_of(value)
    except Exception:  # noqa: BLE001 - 用户塞了怪值
        return ""


def _shade(color: str, factor: float) -> str:
    """把一个 ``"#RRGGBB"`` 按比例压暗 / 提亮；认不出来的原样返回。"""
    if factor == 1.0 or not color.startswith("#") or len(color) != 7:
        return color
    try:
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return color
    clamp = lambda v: max(0, min(255, int(round(v * factor))))  # noqa: E731
    return "#%02x%02x%02x" % (clamp(r), clamp(g), clamp(b))


def _single_map(before: Palette, after: Palette) -> Dict[str, str]:
    """「旧色 → 新色」的替换表。

    控件持有的颜色是构造时取走的字符串，拿不到令牌名，只能按颜色值反查。
    这里只记录本次真正改过的令牌「旧色→新色」，改到谁就换谁；同值令牌
    互不影响（没改的令牌不会出现在表里）。
    """
    mapping: Dict[str, str] = {}
    for name, new in after.items():
        old = before.get(name)
        if old is None or old == new:
            continue
        new_single = _single_color(new)
        if not new_single:
            continue
        # 玻璃模式下令牌被 ``apply_backdrop`` 换成了透明键色，而控件存的
        # 可能是普通基准色，两个都要认。
        olds = {_single_color(old), _single_color(_BASELINE.get(name, ""))}
        for old_single in olds:
            if old_single and old_single != new_single:
                mapping[old_single] = new_single
    return mapping


def _is_color_attr(name: str) -> bool:
    """是不是 CTk 控件里的颜色属性（``_fg_color`` / ``_text_color_disabled``）。"""
    return name.endswith("_color") or "_color_" in name


def _patch_widget(widget: tk.Misc, singles: Mapping[str, str]) -> bool:
    """把控件自己的颜色属性从旧色换成新色；返回是否改过。"""
    changed = False
    for attr, value in list(vars(widget).items()):
        if not _is_color_attr(attr) or not isinstance(value, str):
            continue
        new = singles.get(value)
        if not new or new == value:
            continue
        try:
            setattr(widget, attr, new)
        except Exception:  # noqa: BLE001 - 只读属性之类，跳过
            continue
        changed = True
    return changed


def _walk(widget: tk.Misc):
    """前序遍历控件树（父先子后，父的底色变完再让子跟着变）。"""
    yield widget
    try:
        children = widget.winfo_children()
    except Exception:  # noqa: BLE001 - 已销毁的控件
        return
    for child in children:
        yield from _walk(child)


def _walk_all(root: Optional[tk.Misc] = None):
    """遍历要刷新的所有窗口里的控件。"""
    for top in _targets(root):
        yield from _walk(top)


class Usage(NamedTuple):
    """一处颜色引用：哪个控件的哪个属性用了这个令牌。"""

    widget: tk.Misc
    attr: str
    value: Any

    def describe(self) -> str:
        return f"{self.widget.__class__.__name__}::{self.attr}"


def find_usage(token: str, *, root: Optional[tk.Misc] = None) -> List[Usage]:
    """列出当前界面上哪些控件的颜色属性取自 ``token``。

    只找存在控件属性里的颜色（``_fg_color`` / ``_text_color`` 这类）。纯
    canvas 自绘的部分（开关的轨道、滑块的填充、表格的线）不在属性里，
    要等那个组件实现 ``apply_theme()`` 之后才算得上「带动画地换色」。
    """
    value = getattr(T, token, None)
    if value is None:
        return []
    wanted = {
        _single_color(value),
        _single_color(_BASELINE.get(token, "")),
    } - {""}

    usages: List[Usage] = []
    for widget in _walk_all(root):
        for attr, current in list(vars(widget).items()):
            if not _is_color_attr(attr):
                continue
            if isinstance(current, str):
                if current in wanted:
                    usages.append(Usage(widget, attr, current))
                continue
            if _single_color(current) in wanted:
                usages.append(Usage(widget, attr, current))
    return usages


def usage_summary(token: str, *, root: Optional[tk.Misc] = None) -> Dict[str, int]:
    """``{控件类名: 用到这个令牌的属性个数}``。"""
    summary: Dict[str, int] = {}
    for usage in find_usage(token, root=root):
        name = usage.widget.__class__.__name__
        summary[name] = summary.get(name, 0) + 1
    return summary


def describe_usage(token: str, *, root: Optional[tk.Misc] = None) -> str:
    """一句话说明这个令牌用在了哪些组件上，例如「3 个 CTkButton、2 个 CTkLabel」。"""
    summary = usage_summary(token, root=root)
    total = sum(summary.values())
    if not total:
        return "当前界面没有组件用到"
    parts = [f"{count} 个 {name}" for name, count in sorted(summary.items(), key=lambda kv: (-kv[1], kv[0]))]
    return f"{total} 处：" + "、".join(parts)


def _redraw(widget: tk.Misc) -> None:
    """让 CTk 控件按当前属性重画一遍。"""
    draw = getattr(widget, "_draw", None)
    if callable(draw):
        try:
            draw()
        except Exception:  # noqa: BLE001 - 个别控件正在销毁时重绘会抛
            pass


def _targets(root: Optional[tk.Misc]) -> List[tk.Misc]:
    """要刷新的窗口：传了 root 就只刷它，没传就刷默认根窗口。"""
    if root is not None:
        return [root]
    default = getattr(tk, "_default_root", None)
    return [default] if default is not None else []


def _run_redraws() -> None:
    """跑一遍登记过的自绘控件重绘回调。"""
    for key, (ref, callback) in list(_REDRAW.items()):
        if ref() is None:
            _REDRAW.pop(key, None)
            continue
        try:
            callback()
        except Exception:  # noqa: BLE001 - 已经销毁的自绘控件
            _REDRAW.pop(key, None)


def _repaint(before: Palette, after: Palette, root: Optional[tk.Misc]) -> None:
    """按 before → after 的对应关系刷一遍控件树。"""
    singles = _single_map(before, after)
    for top in _targets(root):
        for widget in _walk(top):
            # 自绘组件（Segmented / 表格 / 圆环…）的颜色画在 canvas 图元或
            # Pillow 图上，换属性没用，得让它按当前令牌整块重画。
            hook = getattr(widget, "apply_theme", None)
            if callable(hook):
                try:
                    hook()
                except Exception:  # noqa: BLE001 - 组件正在销毁或还没布局
                    pass
            if _patch_widget(widget, singles):
                _redraw(widget)
    _run_redraws()


def _sync_sheets(before: Palette, after: Palette) -> None:
    """``styles.SHEETS`` 是导入时的快照，跟着令牌一起换掉。"""
    try:
        from . import styles
    except Exception:  # noqa: BLE001 - 单独用 theming 时没有样式表
        return

    singles = _single_map(before, after)
    for states in styles.SHEETS.values():
        for params in states.values():
            for prop, value in list(params.items()):
                if isinstance(value, str) and value in singles:
                    params[prop] = singles[value]


def _rebase_backdrop(changed: Palette) -> None:
    """同步毛玻璃的「普通底色」基准，切回不透明时覆盖不会丢。"""
    from . import theme

    for name, value in changed.items():
        theme.rebase_token(name, value)


def apply_palette(
    updates: Mapping[str, Any],
    *,
    root: Optional[tk.Misc] = None,
    repaint: bool = True,
    shade: bool = True,
) -> List[str]:
    """把一批颜色令牌换成新值，并让界面就地更新。

    参数:
        updates: ``{令牌名: "#RRGGBB"}``。未知的令牌名会被忽略；传入二元组
            时取最后一项（兼容旧写法）。
        root: 要刷新的窗口；不传就刷默认根窗口（含它的弹出窗口）。
        repaint: 传 ``False`` 时只改令牌、不动已有控件——启动阶段还没建
            控件时用。
        shade: 传 ``True``（默认）时按 :data:`_DARKEN` 压暗自定义色，毛玻璃
            主题下就是「用户挑的颜色实际显示暗 20%」；重置还原时传 ``False``。

    返回:
        实际改掉的令牌名列表（值没变化的不会出现在里面）。
    """
    before = _token_values()
    after = dict(before)
    changed: Palette = {}

    for name, raw in updates.items():
        if name not in before:
            continue
        new = _normalized(raw)
        if new is None:
            continue
        target = _shade(new, _DARKEN) if shade else new
        if before[name] == target:
            _OVERRIDES[name] = new
            continue
        after[name] = target
        changed[name] = target

    if not changed:
        return []

    for name, value in changed.items():
        setattr(T, name, value)
        # 覆盖表里留用户挑的原色，切主题时按新系数重新压暗 / 还原
        _OVERRIDES[name] = _normalized(updates[name]) or value

    _rebase_backdrop(changed)

    # 玻璃模式下窗口底 / 侧边栏必须保持透明键色，否则整窗不再透明。
    # 用户挑的普通底色只记进基准（rebase_token 已做），切回不透明时生效。
    from . import theme

    if theme.current_backdrop() == "acrylic":
        veil = theme.current_veil()
        for name in changed:
            if name in ("COLOR_BG", "COLOR_SIDE"):
                after[name] = veil
                setattr(T, name, veil)

    _sync_sheets(before, after)
    if repaint:
        _repaint(before, after, root)
    return list(changed)


def reset_palette(*, root: Optional[tk.Misc] = None) -> List[str]:
    """把覆盖过的令牌还原成导入时的值。返回还原了哪些令牌。"""
    if not _OVERRIDES:
        return []
    baseline = _baseline()
    updates = {
        name: baseline[name]
        for name in _OVERRIDES
        if name in baseline
    }
    if not updates:
        return []
    changed = apply_palette(updates, root=root, shade=False)
    for name in changed:
        _OVERRIDES.pop(name, None)
    return changed


def set_darken(factor: float, *, root: Optional[tk.Misc] = None) -> None:
    """设定自定义颜色的整体明度系数，并立刻让界面按新系数重画。

    毛玻璃主题下传 ``0.8``（用户挑的颜色实际显示暗 20%），切回其它主题传
    ``1.0`` 还原。只影响被 :func:`apply_palette` 覆盖过的令牌，默认配色不动。
    """
    global _DARKEN
    _DARKEN = max(0.0, min(1.0, float(factor)))
    if not _OVERRIDES:
        return
    before = _token_values()
    after = dict(before)
    for name, base in _OVERRIDES.items():
        if name not in after:
            continue
        target = _shade(base, _DARKEN)
        after[name] = target
        setattr(T, name, target)
    from . import theme

    if theme.current_backdrop() == "acrylic":
        veil = theme.current_veil()
        for name in ("COLOR_BG", "COLOR_SIDE"):
            if name in after:
                after[name] = veil
                setattr(T, name, veil)
    _sync_sheets(before, after)
    _repaint(before, after, root)


def palette_changes() -> Palette:
    """当前被覆盖的令牌；空字典表示全是默认值。"""
    return dict(_OVERRIDES)


def current_palette() -> Palette:
    """``tokens`` 此刻的全部颜色令牌（含覆盖后的值）。"""
    return _token_values()


def refresh(root: Optional[tk.Misc] = None) -> None:
    """不换色，只让界面按当前令牌重绘一遍（自绘控件走登记的回调）。"""
    _run_redraws()
    for top in _targets(root):
        for widget in _walk(top):
            _redraw(widget)


def register_redraw(widget: tk.Misc, callback: Callable[[], Any]) -> None:
    """登记一个自绘控件的重绘函数，换色 / 刷新时会被调用。

    回调应该自己从 ``tokens`` 重新取色再画，不要缓存颜色字符串。
    """
    key = str(widget)

    def _cleanup(_ref: weakref.ref) -> None:
        _REDRAW.pop(key, None)

    _REDRAW[key] = (weakref.ref(widget, _cleanup), callback)


def save_palette(path: str | Path, palette: Mapping[str, Any]) -> None:
    """把调色板写成 JSON：``{"COLOR_ACTIVE": "#606269"}``。

    只写覆盖项，不写全量——读回来时没写的令牌自然沿用默认值。
    """
    data: Dict[str, str] = {}
    for name, value in palette.items():
        color = _normalized(value)
        if color is not None:
            data[name] = color

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_palette(path: str | Path) -> Palette:
    """读回 :func:`save_palette` 写的 JSON；文件不存在或损坏时返回空字典。"""
    target = Path(path)
    if not target.exists():
        return {}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - 配置损坏不该阻止启动
        return {}

    palette: Palette = {}
    if not isinstance(data, dict):
        return palette
    for name, value in data.items():
        color = _normalized(value)
        if color is not None:
            palette[name] = color
    return palette
