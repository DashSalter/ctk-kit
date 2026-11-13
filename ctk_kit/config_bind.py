"""把 ctk-kit 组件绑定到 conf_base 配置项。

conf_base 的配置项（``ConfigProperty`` / ``PropertyProxy``）提供两个接口：
``.value`` 读写当前值，``.on_change(callback)`` 注册
``(section, option, value)`` 变更回调。本模块只依赖这两个接口，不直接
import conf_base。

支持的控件与配置类型：

- 输入框 ``CTkEntry`` / ``CompoundEntry``、文本区 ``TextArea`` ↔ ``str``
- 开关 ``Switch``、勾选 ``Check``、单选 ``Radio`` ↔ ``bool`` 或 ``str``
- 分段选择 ``Segmented``、下拉 ``DropField`` ↔ ``str``
- 步进 ``Spinner``、滑块 ``Slider`` ↔ ``int`` / ``float`` / ``str``

写回是实时的：输入每次按键、开关每次拨动、选择每次切换、步进/滑块每次变化
都会立刻写配置项，conf_base 的 ``set_value`` 在非批量模式下会立即落盘。

任何读 / 写 / 类型转换失败都只警告，不向调用方抛异常，避免配置问题挡住
界面启动。
"""

from __future__ import annotations

import warnings
from typing import Any, Callable, Optional

try:
    from tkinter import Misc as _Misc
except Exception:  # pragma: no cover - 非 Tk 环境仅用于类型标注
    _Misc = object  # type: ignore[assignment,misc]

ErrorHandler = Optional[Callable[[str], None]]

_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "是", "开"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off", "否", "关"})

_KINDS = {
    "CTkEntry": "input",
    "CompoundEntry": "input",
    "TextArea": "textarea",
    "Switch": "flag",
    "Check": "flag",
    "Radio": "flag",
    "Segmented": "choice",
    "DropField": "choice",
    "Spinner": "number",
    "Slider": "number",
}


def _cast(value: Any, default: Any) -> Any:
    """按配置项默认值的类型转换控件值。"""
    kind = type(default)
    if kind is bool:
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in _TRUE_VALUES:
            return True
        if text in _FALSE_VALUES:
            return False
        raise ValueError(f"无法把 {value!r} 转成 bool")
    if kind is int:
        return value if type(value) is int else int(str(value).strip())
    if kind is float:
        return value if type(value) is float else float(str(value).strip())
    if kind is str:
        return value if isinstance(value, str) else str(value)
    if kind in (list, dict):
        return value if isinstance(value, kind) else default
    return value if isinstance(value, kind) else kind(value)


def _name(target: Any) -> str:
    section = getattr(target, "section", "")
    option = getattr(target, "option", "")
    if section and option:
        return f"{section}.{option}"
    return type(target).__name__


def _kind_of(widget: _Misc) -> str:
    """判断控件属于哪一类：input / textarea / flag / choice / number。"""
    kind = _KINDS.get(type(widget).__name__)
    if kind is not None:
        return kind
    # 兜底：按能力猜，认不出来时当作输入框
    if hasattr(widget, "_seg_canvas"):
        return "choice"
    if hasattr(widget, "textbox"):
        return "textarea"
    if hasattr(widget, "get_value") and hasattr(widget, "set_value"):
        try:
            return "flag" if isinstance(widget.get_value(), (bool, str)) else "number"
        except Exception:  # noqa: BLE001
            return "flag"
    if hasattr(widget, "get") and hasattr(widget, "set"):
        return "input"
    return "input"


class _Binding:
    """一个控件与一个配置项之间的双向绑定。"""

    def __init__(
            self, widget: _Misc, target: Any, on_error: ErrorHandler = None
    ) -> None:
        self.widget = widget
        self.target = target
        self._on_error = on_error
        self._closed = False
        self._syncing = False
        self._kind = _kind_of(widget)
        self._original_command: Any = None
        self._original_on_change: Any = None

    # ------------------------------------------------------------------ 建立
    def open(self) -> "_Binding":
        """校验类型、读一次配置填进控件，再挂上双向监听。"""
        if not self._check_kind():
            self._closed = True
            return self
        self._fill()
        if self._kind == "flag":
            self._hook_flag()
        elif self._kind in ("choice", "number"):
            self._hook_command_value()
        elif self._kind == "textarea":
            self._hook_textarea()
        else:
            self._hook_input()
        self._hook_target()
        self._watch_destroy()
        return self

    def _check_kind(self) -> bool:
        """按控件类别检查配置项默认值的类型，不匹配就跳过绑定。"""
        default = getattr(self.target, "default", None)
        kind = type(default)
        if self._kind == "flag":
            if kind not in (bool, str):
                self._warn(
                    f"开关/勾选/单选只能绑定 bool 或 str 配置，"
                    f"{_name(self.target)} 的默认值是 {kind.__name__}，已跳过绑定"
                )
                return False
        elif self._kind == "number":
            if kind not in (int, float, str):
                self._warn(
                    f"步进/滑块只能绑定 int、float 或 str 配置，"
                    f"{_name(self.target)} 的默认值是 {kind.__name__}，已跳过绑定"
                )
                return False
        elif kind is not str:
            label = {
                "input": "输入框",
                "textarea": "文本区",
                "choice": "分段选择/下拉",
            }.get(self._kind, "控件")
            self._warn(
                f"{label}只能绑定 str 配置，{_name(self.target)} 的默认值是 "
                f"{kind.__name__}，已跳过绑定"
            )
            return False
        return True

    def _fill(self) -> None:
        try:
            value = self.target.value
        except Exception as exc:  # noqa: BLE001 - 配置坏了也要能起界面
            self._warn(f"读取配置 {_name(self.target)} 失败，使用默认值：{exc}")
            value = getattr(self.target, "default", None)
        try:
            self._write(value)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"初始化控件 {_name(self.target)} 失败：{exc}")

    def _hook_flag(self) -> None:
        """开关/勾选/单选：command 不带参数，先跑原回调再写配置。"""
        self._original_command = getattr(self.widget, "_command", None)

        def command() -> None:
            original = self._original_command
            if original is not None:
                try:
                    original()
                except Exception as exc:  # noqa: BLE001
                    self._warn(f"控件原 command 执行失败：{exc}")
            self._push()

        try:
            self.widget._command = command
        except Exception as exc:  # noqa: BLE001
            self._warn(f"绑定开关/勾选失败：{exc}")

    def _hook_command_value(self) -> None:
        """分段选择/下拉/步进/滑块：command 带新值参数。"""
        self._original_command = getattr(self.widget, "_command", None)

        def command(value: Any) -> None:
            original = self._original_command
            if original is not None:
                try:
                    original(value)
                except Exception as exc:  # noqa: BLE001
                    self._warn(f"控件原 command 执行失败：{exc}")
            self._push()

        try:
            self.widget._command = command
        except Exception as exc:  # noqa: BLE001
            self._warn(f"绑定选择控件失败：{exc}")

    def _hook_textarea(self) -> None:
        """文本区自有 on_change 回调，包一层即可。"""
        self._original_on_change = getattr(self.widget, "_on_change", None)

        def on_change(text: str) -> None:
            original = self._original_on_change
            if original is not None:
                try:
                    original(text)
                except Exception as exc:  # noqa: BLE001
                    self._warn(f"文本区原 on_change 执行失败：{exc}")
            self._push()

        try:
            self.widget._on_change = on_change
        except Exception as exc:  # noqa: BLE001
            self._warn(f"绑定文本区失败：{exc}")

    def _hook_input(self) -> None:
        """输入框绑在内部 tk.Entry 上：焦点和按键事件都在它身上。"""
        widget = self.widget
        entry = getattr(widget, "_entry", None)
        if entry is None:
            inner = getattr(widget, "entry", None)
            entry = getattr(inner, "_entry", inner) if inner is not None else widget
        for sequence in ("<KeyRelease>", "<FocusOut>"):
            try:
                entry.bind(sequence, self._on_event, add="+")
            except Exception as exc:  # noqa: BLE001
                self._warn(f"绑定输入事件 {sequence} 失败：{exc}")

    def _hook_target(self) -> None:
        on_change = getattr(self.target, "on_change", None)
        if on_change is None:
            return
        try:
            on_change(self._on_target_change)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"监听配置 {_name(self.target)} 失败：{exc}")

    def _watch_destroy(self) -> None:
        try:
            self.widget.bind("<Destroy>", self._on_destroy, add="+")
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ 回调
    def _on_event(self, _event: Any = None) -> None:
        if self._closed or self._syncing:
            return
        self._push()

    def _on_target_change(self, section: str, option: str, value: Any) -> None:
        if self._closed or self._syncing:
            return
        try:
            self._write(value)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"同步配置 {section}.{option} 到控件失败：{exc}")

    def _on_destroy(self, event: Any) -> None:
        # CTk 的 bind 可能转发到内部控件，event.widget 不一定是外框；
        # 只要收到 Destroy 就停止同步，避免解绑绑到已销毁的控件上。
        self.close()

    # ------------------------------------------------------------------ 读写
    def _read(self) -> Any:
        if self._kind == "flag":
            return self.widget.get_value()
        return self.widget.get()

    def _write(self, value: Any) -> None:
        if self._kind == "flag":
            self.widget.set_value(value)
        else:
            self.widget.set(value)

    def _push(self) -> None:
        try:
            raw = self._read()
            value = _cast(raw, self.target.default)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"把控件值写入配置 {_name(self.target)} 失败：{exc}")
            return
        try:
            current = self.target.value
        except Exception:  # noqa: BLE001
            current = object()
        if type(current) is type(value) and current == value:
            return
        self._syncing = True
        try:
            self.target.value = value
        except Exception as exc:  # noqa: BLE001
            self._warn(f"写配置 {_name(self.target)} 失败：{exc}")
        finally:
            self._syncing = False

    # ------------------------------------------------------------------ 收尾
    def close(self) -> None:
        """停止同步；控件销毁时自动调用。"""
        if self._closed:
            return
        self._closed = True
        if self._kind == "textarea":
            if self._original_on_change is not None:
                try:
                    self.widget._on_change = self._original_on_change
                except Exception:  # noqa: BLE001
                    pass
            return
        if self._original_command is not None:
            try:
                self.widget._command = self._original_command
            except Exception:  # noqa: BLE001
                pass

    def _warn(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)
        else:
            warnings.warn(message, RuntimeWarning, stacklevel=3)


def bind_config(
        widget: _Misc, target: Any, *, on_error: ErrorHandler = None
) -> _Binding:
    """把输入类控件绑定到 conf_base 配置项。

    支持的控件：``CTkEntry``、``CompoundEntry``、``TextArea``、``Switch``、
    ``Check``、``Radio``、``Segmented``、``DropField``、``Spinner``、``Slider``。

    参数:
        widget: 上面列出的控件之一。
        target: 配置项，例如 ``UiPrefs.nickname``（``PropertyProxy``）。
        on_error: 自定义错误处理；默认 ``warnings.warn``，不会抛异常。

    返回:
        绑定对象；``close()`` 可手动解绑（控件销毁时也会自动解绑）。
    """
    old = getattr(widget, "_config_binding", None)
    if isinstance(old, _Binding):
        old.close()
    binding = _Binding(widget, target, on_error=on_error).open()
    try:
        widget._config_binding = binding
    except Exception:  # noqa: BLE001
        pass
    return binding


def unbind_config(widget: _Misc) -> None:
    """解除 :func:`bind_config` 建立的双向绑定。"""
    old = getattr(widget, "_config_binding", None)
    if isinstance(old, _Binding):
        old.close()
    try:
        widget._config_binding = None
    except Exception:  # noqa: BLE001
        pass
