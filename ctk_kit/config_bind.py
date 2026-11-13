"""把 ctk-kit 组件绑定到 conf_base 配置项。

conf_base 的配置项（``ConfigProperty`` / ``PropertyProxy``）提供两个接口：
``.value`` 读写当前值，``.on_change(callback)`` 注册
``(section, option, value)`` 变更回调。本模块只依赖这两个接口，不直接
import conf_base。

写回是实时的：``Entry`` 每次按键、``Switch`` 每次拨动都会立刻写配置项，
conf_base 的 ``set_value`` 在非批量模式下会立即落盘。

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
        # Switch 有 toggle()；Entry 没有。只靠 get_value/set_value 判断会把
        # 继承了 Enablable 的输入框也误认成开关。
        self._switch = (
            hasattr(widget, "get_value")
            and hasattr(widget, "set_value")
            and hasattr(widget, "toggle")
        )
        self._original_command: Any = None

    # ------------------------------------------------------------------ 建立
    def open(self) -> "_Binding":
        """读一次配置填进控件，再挂上双向监听。"""
        self._fill()
        if self._switch:
            self._hook_switch()
        else:
            self._hook_entry()
        self._hook_target()
        self._watch_destroy()
        return self

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

    def _hook_switch(self) -> None:
        """包一层 command：先跑用户自己的回调，再把新状态写回配置。"""
        self._original_command = getattr(self.widget, "_command", None)

        def command() -> None:
            original = self._original_command
            if original is not None:
                try:
                    original()
                except Exception as exc:  # noqa: BLE001
                    self._warn(f"开关原 command 执行失败：{exc}")
            self._push()

        try:
            self.widget.configure(command=command)
        except Exception as exc:  # noqa: BLE001
            self._warn(f"绑定开关失败：{exc}")

    def _hook_entry(self) -> None:
        """输入框绑在内部 tk.Entry 上：焦点和按键事件都在它身上。"""
        target = getattr(self.widget, "_entry", self.widget)
        for sequence in ("<KeyRelease>", "<FocusOut>"):
            try:
                target.bind(sequence, self._on_event, add="+")
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
        if getattr(event, "widget", None) is self.widget:
            self.close()

    # ------------------------------------------------------------------ 读写
    def _read(self) -> Any:
        if self._switch:
            return bool(self.widget.get_value())
        return self.widget.get()

    def _write(self, value: Any) -> None:
        if self._switch:
            self.widget.set_value(bool(value))
        elif hasattr(self.widget, "set"):
            self.widget.set("" if value is None else str(value))

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
        if self._switch and self._original_command is not None:
            try:
                self.widget.configure(command=self._original_command)
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
    """把 ``Entry`` / ``Switch`` 绑定到 conf_base 配置项。

    参数:
        widget: ``CTkEntry`` 或 ``Switch``。
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
