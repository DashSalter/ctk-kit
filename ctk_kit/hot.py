# -*- coding: utf-8 -*-
"""热更新窗口：用法和 :class:`App` 完全一样，只是换个名字。

::

    import ctk_kit as ctk

    TOOLBAR = [("开始", 110, 40), ("暂停", 96, 36)]

    app = ctk.HotApp(title="演示", size=(900, 640))

    page = ctk.Frame(app)
    page.pack(fill="both", expand=True, padx=24, pady=20)
    for text, width in TOOLBAR:
        ctk.PrimaryButton(page, text, width=width).pack(side="left")

    app.mainloop()

保存这个文件后，``mainloop()`` 里的监听会发现变化并重新执行它：新代码里的
控件与上一版逐个比对，参数变了的就地写进旧控件，多的删、缺的补，其余控件
（含输入内容、滚动位置）保持不动。语句结构大改或某个参数没法就地改时，自动
整页重建。

约定：

* 场景代码就是普通的顶层代码，不用包装成函数或类；控件直接建在 ``app``
  上即可；
* 模块顶层只放常量、import 和界面代码，不要做有副作用的操作——热更新会
  重新执行一遍；
* ``app.auto_rebuild`` 设成 ``False`` 暂停监听，``app.reload()`` 仍可手动
  更新；
* 同一个进程只会有一个 ``HotApp`` 实例，重载时再次执行 ``HotApp(...)`` 和
  ``mainloop()`` 都会落到既有窗口上。

程序只能读磁盘上的文件，编辑器里还没保存的改动读不到；打开编辑器的自动
保存（VS Code 的 ``files.autoSave``）就能边改边刷新。
"""

from __future__ import annotations

import ast
import functools
import inspect
import os
import sys
import tkinter as tk
import traceback
from pathlib import Path
from typing import Any, Optional

from .window import App as _App

# 这里拿到的永远是真实模块：即使热更新期间 ``sys.modules["ctk_kit"]`` 被换成了
# 代理，这个引用也不会变，代理才能安全地查到真实控件工厂。
import ctk_kit as _kit

__all__ = ["HotApp"]

_HERE = Path(__file__).resolve()
#: 当前正在热更新的场景文件，供 ``_scene_line`` 定位调用行。
_SCENE: Optional[Path] = None
#: 正在执行的构建器；``None`` 表示试跑或普通创建。
_CURRENT: Optional["_Builder"] = None


class _Fallback(Exception):
    """某个变化没法就地应用，退回到整页重建。"""


class _Record:
    """上一次构建时某个控件的创建信息。"""

    __slots__ = ("widget", "parent", "key", "name", "params")

    def __init__(self, widget: Any, parent: Any, key: str, name: str,
                 params: dict[str, Any]) -> None:
        self.widget = widget
        self.parent = parent
        self.key = key
        self.name = name
        self.params = params


_MISSING = object()


@functools.lru_cache(maxsize=None)
def _signature(factory: Any) -> Any:
    """工厂的参数签名；拿不到就返回 ``None``。"""
    try:
        return inspect.signature(factory)
    except (TypeError, ValueError):
        return None


def _bind(factory: Any, args: tuple[Any, ...],
          kwargs: dict[str, Any]) -> Optional[dict[str, Any]]:
    """把一次工厂调用按参数名摊平，位置参数和关键字参数一视同仁。"""
    signature = _signature(factory)
    if signature is None:
        return None
    try:
        bound = signature.bind(*args, **kwargs)
    except TypeError:
        return None
    bound.apply_defaults()
    params: dict[str, Any] = {}
    for name, param in signature.parameters.items():
        if name == "master" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name in bound.arguments:
            params[name] = bound.arguments[name]
    return params


def _diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """新旧创建参数里不一致、需要写到旧控件上的部分。"""
    changes: dict[str, Any] = {}
    for key, value in new.items():
        before = old.get(key, _MISSING)
        if before is _MISSING:
            changes[key] = value
        elif callable(value) or callable(before):
            # 回调每次都是新函数对象，交给 configure 换成新闭包。
            changes[key] = value
        else:
            try:
                if before != value:
                    changes[key] = value
            except Exception:  # noqa: BLE001 - 不可比较的对象按「变了」处理
                changes[key] = value
    return changes


def _same_params(old: dict[str, Any], new: dict[str, Any]) -> bool:
    """除回调外的参数是否完全一致，用来优先复用「同一个」旧控件。"""
    for key, value in new.items():
        if callable(value):
            continue
        before = old.get(key, _MISSING)
        if before is _MISSING or callable(before):
            return False
        try:
            if before != value:
                return False
        except Exception:  # noqa: BLE001
            return False
    return True


def _scene_line() -> Optional[int]:
    """当前这次控件创建发生在场景文件的哪一行。"""
    target = None if _SCENE is None else str(_SCENE)
    frame = sys._getframe(1)
    while frame is not None:
        if frame.f_code.co_filename == target:
            return frame.f_lineno
        frame = frame.f_back
    return None


def _skeleton(node: ast.stmt) -> str:
    """语句骨架：常量抹掉，只留结构。

    这样改数字、改字符串不会被当成结构变化；同一行循环创建的控件也能按
    顺序对上。
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant):
            sub.value = "?"
            sub.kind = None
    return ast.dump(node)


def _stmt_map(source: str) -> dict[int, str]:
    """行号 → 该行所属最小语句的骨架。"""
    tree = ast.parse(source)
    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.stmt)]
    nodes.sort(key=lambda node: -((node.end_lineno or node.lineno) - node.lineno))
    mapping: dict[int, str] = {}
    for node in nodes:
        key = _skeleton(node)
        for line in range(node.lineno, (node.end_lineno or node.lineno) + 1):
            mapping[line] = key
    return mapping


class _Builder:
    """执行一次场景构建：能复用旧控件就复用，否则新建。"""

    def __init__(self, stmt_map: dict[int, str], old_records: list[_Record]) -> None:
        self.stmt_map = stmt_map
        self.old_records = list(old_records)
        self.records: list[_Record] = []
        self.used: set[int] = set()
        self.updated = 0
        self.created = 0
        self.removed = 0
        self.index: dict[tuple[int, str, str], list[_Record]] = {}
        for record in self.old_records:
            slot = (id(record.parent), record.key, record.name)
            self.index.setdefault(slot, []).append(record)

    def make(self, factory: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        """控件工厂的替身：先找旧控件，找不到才真的创建。"""
        line = _scene_line()
        key = self.stmt_map.get(line) if line is not None else None
        parent = args[0] if args else kwargs.get("master")
        if key is None or not isinstance(parent, tk.Misc):
            return factory(*args, **kwargs)

        params = _bind(factory, args, kwargs)
        if params is None:  # 签名拿不到就不做复用，避免留下旧内容
            return factory(*args, **kwargs)

        name = getattr(factory, "__name__", type(factory).__name__)
        record = self._take(parent, key, name, params)
        if record is None:
            widget = factory(*args, **kwargs)
            if isinstance(widget, tk.Misc):
                self.records.append(_Record(widget, parent, key, name, params))
                self.created += 1
            return widget

        changes = _diff(record.params, params)
        if changes:
            try:
                record.widget.configure(**changes)
            except Exception:  # noqa: BLE001 - 不能就地改，退回整页重建
                raise _Fallback from None
            self.updated += 1
        record.params = params
        self.used.add(id(record.widget))
        self.records.append(record)
        return record.widget

    def _take(self, parent: Any, key: str, name: str,
              params: dict[str, Any]) -> Optional[_Record]:
        """同一父控件下按顺序挑旧控件，参数相同的优先。"""
        candidates = []
        for record in self.index.get((id(parent), key, name), ()):
            if id(record.widget) in self.used:
                continue
            try:
                if record.widget.winfo_exists():
                    candidates.append(record)
            except Exception:  # noqa: BLE001
                continue
        for record in candidates:
            if _same_params(record.params, params):
                return record
        return candidates[0] if candidates else None

    def sweep(self) -> None:
        """销毁这次没被用上的旧控件（代码里删掉的）。"""
        for record in self.old_records:
            if id(record.widget) in self.used:
                continue
            try:
                if record.widget.winfo_exists():
                    record.widget.destroy()
                    self.removed += 1
            except Exception:  # noqa: BLE001
                pass


class _FakeWidget:
    """试跑用的假控件：任何属性、调用都继续返回假控件，什么都不真的做。"""

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__"):
            raise AttributeError(name)
        return _FakeWidget()

    def __call__(self, *args: Any, **kwargs: Any) -> "_FakeWidget":
        return _FakeWidget()

    def __iter__(self) -> Any:
        return iter(())


class _Proxy:
    """场景里的 ``ctk``：记录控件创建；试跑时发假控件。"""

    #: 这些是窗口类，要按真实类交给场景（可能要继承），不能包装成函数。
    _SKIP = frozenset({"App", "HotApp", "CTk", "Notifier"})

    def __getattr__(self, name: str) -> Any:
        target = getattr(_kit, name)
        if not callable(target) or name in self._SKIP:
            return target

        def call(*args: Any, **kwargs: Any) -> Any:
            if HotApp._dry:
                return _FakeWidget()
            builder = _CURRENT
            if builder is None:
                return target(*args, **kwargs)
            return builder.make(target, args, kwargs)

        return call


_PROXY = _Proxy()


def _caller_file() -> Optional[Path]:
    """场景文件路径：调用栈里第一个不是本文件的源码。"""
    frame = sys._getframe(1)
    while frame is not None:
        try:
            path = Path(frame.f_code.co_filename).resolve()
        except (OSError, ValueError):
            path = None
        if path is not None and path != _HERE:
            return path
        frame = frame.f_back
    return None


class HotApp(_App):
    """用法与 :class:`App` 相同的热更新窗口。

    参数:
        scene: 要监听的场景文件，默认取创建窗口的那个源码文件。
        check_ms: 轮询间隔（毫秒），默认 300。
        **kwargs: 其余参数原样交给 :class:`App`，例如 ``title`` / ``size`` /
            ``appearance``。

    注意:
        同一进程只有一个实例：重载时场景代码再次执行 ``HotApp(...)`` 会拿到
        既有窗口；再次调用 ``mainloop()`` 也不会重复进入。
    """

    #: 进程内唯一实例。
    _live: Optional["HotApp"] = None
    #: 试跑模式：``HotApp(...)`` 返回假控件，不碰真实窗口。
    _dry = False

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if HotApp._dry:
            return _FakeWidget()
        live = HotApp._live
        if live is not None:
            return live
        return super().__new__(cls)

    def __init__(self, *, scene: Any = None, check_ms: int = 300,
                 **kwargs: Any) -> None:
        global _SCENE
        if HotApp._live is self:
            # 重载时场景代码会再执行一次 HotApp(...)；窗口已存在，只同步标题/尺寸。
            title = kwargs.get("title")
            if title:
                self.title(str(title))
            size = kwargs.get("size")
            if size:
                self.geometry(f"{int(size[0])}x{int(size[1])}")
            return

        super().__init__(**kwargs)
        HotApp._live = self
        path = Path(scene) if scene is not None else _caller_file()
        if path is None:
            path = Path(sys.argv[0])
        self._scene = path.resolve()
        _SCENE = self._scene
        self._check_ms = check_ms
        self._running = False
        self._stamp: Optional[tuple[int, int]] = None
        self._records: list[_Record] = []
        #: 设成 False 就暂停监听，只响应 ``reload()``。
        self.auto_rebuild = True

    # ---- 对外 -------------------------------------------------------------

    @property
    def scene_path(self) -> str:
        """被监听的场景文件路径。"""
        return str(self._scene)

    def reload(self) -> None:
        """手动重新读文件并更新一次。

        延后到下一轮事件循环再执行：按钮的 command 正在跑，直接改动它自己
        所在的页面容易踩到已失效的 Tk 命令。
        """
        self.after(1, self._reload_now)

    def open_scene(self) -> None:
        """用系统默认程序打开场景文件。"""
        try:
            os.startfile(self._scene)  # type: ignore[attr-defined]
        except OSError as exc:
            self.notify(f"打不开文件：{exc}", level="error")

    def mainloop(self, *args: Any, **kwargs: Any) -> None:
        """启动界面并开始监听；重载时再次调用不会重复进入。"""
        if self._running:
            return
        self._running = True
        self._bootstrap()
        self._tick()
        super().mainloop(*args, **kwargs)

    # ---- 构建 -------------------------------------------------------------

    def _bootstrap(self) -> None:
        """首次启动：顶层代码已经用真实模块建过一遍控件，清掉按记录模式重建。"""
        self._stamp = self._file_stamp()
        try:
            source = self._scene.read_text(encoding="utf-8")
        except OSError as exc:
            self._report(exc)
            return
        self._clear()
        self._exec_and_apply(source)

    def _exec_and_apply(self, source: str) -> bool:
        """在代理环境下执行场景代码：先增量更新，失败就清空整页重建。"""
        global _CURRENT
        try:
            stmt_map = _stmt_map(source)
        except SyntaxError as exc:
            self._report(exc)
            return False

        previous = self._records
        for attempt in range(2):
            builder = _Builder(stmt_map, [] if attempt else previous)
            real = sys.modules.get("ctk_kit")
            sys.modules["ctk_kit"] = _PROXY
            _CURRENT = builder
            try:
                scope: dict[str, Any] = {
                    "__file__": str(self._scene),
                    "__name__": "hot_scene",
                    "__package__": None,
                }
                exec(compile(source, str(self._scene), "exec"), scope)
            except _Fallback:
                self._clear()
                continue
            except Exception as exc:  # noqa: BLE001 - 场景代码运行出错
                self._records = previous
                self._report(exc)
                return False
            finally:
                _CURRENT = None
                sys.modules["ctk_kit"] = real
            builder.sweep()
            self._records = builder.records
            return True

        self._records = previous
        return False

    def _clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._records = []

    # ---- 监听 -------------------------------------------------------------

    def _file_stamp(self) -> Optional[tuple[int, int]]:
        try:
            info = self._scene.stat()
        except OSError:
            return None
        return info.st_mtime_ns, info.st_size

    def _tick(self) -> None:
        self._check()
        self.after(self._check_ms, self._tick)

    def _check(self) -> None:
        if not self.auto_rebuild:
            return
        stamp = self._file_stamp()
        if stamp is not None and stamp != self._stamp:
            self._reload_now()

    def _reload_now(self) -> None:
        """重新执行场景文件，把新代码应用到当前窗口。"""
        stamp = self._file_stamp()
        if stamp is None:
            return
        try:
            source = self._scene.read_text(encoding="utf-8")
        except OSError as exc:
            self._report(exc)
            return

        self._stamp = stamp
        if not self._dry_run(source):
            return
        self._exec_and_apply(source)

    def _dry_run(self, source: str) -> bool:
        """用假控件试跑一遍：语法或运行时错误就不动旧界面。"""
        real = sys.modules.get("ctk_kit")
        old_dry = HotApp._dry
        HotApp._dry = True
        sys.modules["ctk_kit"] = _PROXY
        try:
            scope: dict[str, Any] = {
                "__file__": str(self._scene),
                "__name__": "hot_scene",
                "__package__": None,
            }
            exec(compile(source, str(self._scene), "exec"), scope)
            return True
        except Exception as exc:  # noqa: BLE001
            self._report(exc)
            return False
        finally:
            HotApp._dry = old_dry
            sys.modules["ctk_kit"] = real

    def _report(self, exc: Exception) -> None:
        traceback.print_exc()
        detail = f"{type(exc).__name__}: {exc}"
        if len(detail) > 120:
            detail = detail[:120] + "…"
        self.notify(f"构建失败：{detail}", level="error")
