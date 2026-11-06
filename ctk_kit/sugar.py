"""给控件补几个短方法：``disable()`` / ``set_text("…")`` / ``set_fg_color("…")``。

原生 Tk 的写法是 ``widget.configure(text="保存")``——每次都要拼选项名，
读值还得 ``cget("text")``。这里把选项名收成 ``set_*`` / ``get_*`` 方法：

```python
btn.set_text("保存")          # 等价于 btn.configure(text="保存")
btn.set_fg_color("#ef4444")   # 等价于 btn.configure(fg_color="#ef4444")
btn.set_font(("微软雅黑", 15)) # 任意 configure 支持的选项都行
btn.set_text("保存").set_fg_color("#4f46e5")   # 返回自己，可以连着写

btn.get_text()                # 读回，等价于 btn.cget("text")
btn.get_fg_color()

btn.disable()                 # 等价于 btn.configure(state="disabled")
btn.enable()
btn.toggle_enabled()
btn.is_enabled()
```

混入方式：

```python
class CTkButton(Enablable, Textual, ctk.CTkButton): ...
```

CTk 原生控件（``CTkButton`` / ``CTkEntry`` …）的 ``state`` 选项本来就有，
混入后直接用；自绘控件没有 ``state``，只要覆盖 ``_apply_enabled()``：
``Switch`` / ``Check`` / ``Radio`` 就是各自把 ``_enabled`` 画成灰态。
"""

from __future__ import annotations

from typing import Any

__all__ = ["Bindable", "Enablable", "Options", "Textual", "Valuable"]

#: 不用带后缀也认识的选项名；``*_color`` 会自动算进来。
_OPTIONS = frozenset({
    "anchor",
    "border_spacing",
    "border_width",
    "command",
    "compound",
    "corner_radius",
    "font",
    "height",
    "image",
    "justify",
    "label",
    "number_of_steps",
    "offvalue",
    "onvalue",
    "orientation",
    "placeholder_text",
    "progress_color",
    "state",
    "text",
    "textvariable",
    "value",
    "values",
    "variable",
    "width",
    "wraplength",
})


def _is_option(name: str) -> bool:
    """这个名字能不能当成 ``set_*`` / ``get_*`` 用。"""
    return name in _OPTIONS or name.endswith("_color")


class Valuable:
    """把 ``get()`` / ``set()`` 统一成 ``get_value()`` / ``set_value()``。

    值可以是任何东西：开关是 ``True`` / ``False``、单选是选项文字、
    范围滑块是 ``(下限, 上限)``、日期控件是 ``date`` / ``time`` 对象。
    没有 ``get()`` 或 ``set()`` 的控件会直接报 ``AttributeError``。
    """

    def get_value(self) -> Any:
        """读当前值，等价于 ``get()``。"""
        getter = getattr(self, "get", None)
        if not callable(getter):
            raise AttributeError(f"{type(self).__name__!r} 没有 get()")
        return getter()

    def set_value(self, value: Any) -> None:
        """设当前值，等价于 ``set(value)``。"""
        setter = getattr(self, "set", None)
        if not callable(setter):
            raise AttributeError(f"{type(self).__name__!r} 没有 set()")
        return setter(value)


class Options(Valuable):
    """把控件选项收成 ``set_xxx(value)`` / ``get_xxx()``。

    只认 ``_OPTIONS`` 里的名字和 ``*_color`` 后缀，其它属性照旧报
    ``AttributeError``——例如 ``getattr(widget, "apply_theme", None)``
    仍然是 ``None``，不会把探测逻辑带偏。

    ``get_value()`` / ``set_value()`` 是真正的办法（不走选项名），
    见 :class:`Valuable`。
    """

    def __getattr__(self, name: str) -> Any:
        if name.startswith("set_"):
            option = name[4:]
            if _is_option(option):
                return _OptionSetter(self, option)
        elif name.startswith("get_"):
            option = name[4:]
            if _is_option(option):
                return _OptionGetter(self, option)
        raise AttributeError(f"{type(self).__name__!r} 没有属性 {name!r}")


class _OptionSetter:
    """``btn.set_text`` 拿到的可调用对象：设完返回控件自己。"""

    __slots__ = ("_widget", "_name")

    def __init__(self, widget: Any, name: str) -> None:
        self._widget = widget
        self._name = name

    def __call__(self, value: Any) -> Any:
        self._widget.configure(**{self._name: value})
        return self._widget

    def __repr__(self) -> str:
        return f"<setter {self._name!r} of {type(self._widget).__name__}>"


class _OptionGetter:
    """``btn.get_text`` 拿到的可调用对象：读当前选项值。"""

    __slots__ = ("_widget", "_name")

    def __init__(self, widget: Any, name: str) -> None:
        self._widget = widget
        self._name = name

    def __call__(self) -> Any:
        return self._widget.cget(self._name)

    def __repr__(self) -> str:
        return f"<getter {self._name!r} of {type(self._widget).__name__}>"


class Bindable:
    """把事件名收成方法，省掉记 ``"<Button-1>"`` 这类字符串。

    处理方法收到的是 Tk 事件对象（有 ``x`` / ``y`` / ``width`` / ``widget``）；
    传 ``None`` 表示解绑。

    ```python
    btn.on_click(lambda event: print(event.x, event.y))
    btn.on_double_click(lambda event: ...)
    btn.on_right_click(lambda event: ...)
    btn.on_enter(lambda event: ...)      # 鼠标移入
    btn.on_leave(lambda event: ...)      # 鼠标移出
    app.on_resize(lambda event: ...)     # 宽或高变了才触发
    app.on_move(lambda event: ...)       # 位置变了才触发
    ```
    """

    def on_click(self, handler: Any) -> Any:
        """鼠标左键按下；``handler(event)``。"""
        return self._bind_event("<Button-1>", handler)

    def on_double_click(self, handler: Any) -> Any:
        """鼠标左键双击。"""
        return self._bind_event("<Double-Button-1>", handler)

    def on_right_click(self, handler: Any) -> Any:
        """鼠标右键按下。"""
        return self._bind_event("<Button-3>", handler)

    def on_enter(self, handler: Any) -> Any:
        """鼠标移入。"""
        return self._bind_event("<Enter>", handler)

    def on_leave(self, handler: Any) -> Any:
        """鼠标移出。"""
        return self._bind_event("<Leave>", handler)

    def on_drag(self, handler: Any) -> Any:
        """按住左键拖动。"""
        return self._bind_event("<B1-Motion>", handler)

    def on_focus(self, handler: Any) -> Any:
        """键盘焦点进入。"""
        return self._bind_event("<FocusIn>", handler)

    def on_blur(self, handler: Any) -> Any:
        """键盘焦点离开。"""
        return self._bind_event("<FocusOut>", handler)

    def on_key(self, handler: Any) -> Any:
        """任意键按下；用 ``event.keysym`` 判断是哪个键。"""
        return self._bind_event("<Key>", handler)

    def on_key_release(self, handler: Any) -> Any:
        """按键松开（做输入框实时筛选时用）。"""
        return self._bind_event("<KeyRelease>", handler)

    def on_scroll(self, handler: Any) -> Any:
        """鼠标滚轮；Windows 上是 ``<MouseWheel>``。"""
        return self._bind_event("<MouseWheel>", handler)

    def on_resize(self, handler: Any) -> Any:
        """宽或高变化时回调；拖动窗口边缘会连续触发。"""
        return self._bind_configure("resize", handler)

    def on_move(self, handler: Any) -> Any:
        """位置变化时回调（窗口拖动、控件换位置）。"""
        return self._bind_configure("move", handler)

    def _bind_event(self, sequence: str, handler: Any) -> Any:
        """绑 / 解绑一个事件，返回控件自己。"""
        if handler is None:
            self.unbind(sequence)
        else:
            # 用 "+" 追加，别把别人（比如 App 的冻结布局）绑在同一个事件上的
            # 回调顶掉：tkinter 默认是替换。
            self.bind(sequence, handler, "+")
        return self

    def _bind_configure(self, kind: str, handler: Any) -> Any:
        """``<Configure>`` 一个事件同时表示「移动」和「改尺寸」，这里拆开分发。"""
        watchers = self.__dict__.get("_configure_watchers")
        if watchers is None:
            watchers = self.__dict__["_configure_watchers"] = {}
        if handler is None:
            watchers.pop(kind, None)
            if not watchers:
                self.__dict__.pop("_configure_last", None)
                self.__dict__["_configure_bound"] = False
            return self
        watchers[kind] = handler
        if not self.__dict__.get("_configure_bound", False):
            self.__dict__["_configure_bound"] = True
            # 同上：追加绑定，避免覆盖 App 冻结布局自己绑的 <Configure>。
            self.bind("<Configure>", self._dispatch_configure, "+")
        return self

    def _dispatch_configure(self, event: Any) -> None:
        """比较上一次的尺寸 / 位置，只把真正变了的那一项交给回调。"""
        watchers = self.__dict__.get("_configure_watchers") or {}
        last = self.__dict__.get("_configure_last")
        size = (event.width, event.height)
        # 顶层窗口的 x / y 就是屏幕位置；普通控件是相对父容器的位置。
        # x_root / y_root 在 Configure 事件里是 "??"，不能用来判断。
        position = (event.x, event.y)
        self.__dict__["_configure_last"] = (size, position)
        if last is None:
            return  # 第一次只记起点，不算变化
        last_size, last_position = last
        if size != last_size and "resize" in watchers:
            watchers["resize"](event)
        if position != last_position and "move" in watchers:
            watchers["move"](event)


class Enablable(Options):
    """把「启用 / 禁用」收成方法。"""

    def enable(self) -> "Enablable":
        """启用控件，返回自己（可以接着写别的）。"""
        return self.set_enabled(True)

    def disable(self) -> "Enablable":
        """禁用控件：鼠标点不动，视觉上变灰，返回自己。"""
        return self.set_enabled(False)

    def toggle_enabled(self) -> "Enablable":
        """在启用 / 禁用之间切换，返回自己。"""
        return self.set_enabled(not self.is_enabled())

    def set_enabled(self, enabled: bool) -> "Enablable":
        """按布尔值设置启用状态，返回自己。

        参数:
            enabled: ``True`` 启用，``False`` 禁用。
        """
        self._enabled = bool(enabled)
        self._apply_enabled(bool(enabled))
        return self

    def is_enabled(self) -> bool:
        """当前是否可用。"""
        try:
            state = self.cget("state")
        except Exception:  # noqa: BLE001 - 自绘控件没有 state 选项
            return bool(getattr(self, "_enabled", True))
        return str(state) != "disabled"

    def _apply_enabled(self, enabled: bool) -> None:
        """真正落地状态。CTk 原生控件走 ``state`` 选项。"""
        try:
            self.configure(state="normal" if enabled else "disabled")
        except Exception:  # noqa: BLE001 - 控件不支持 state 时交给子类
            pass


class Textual(Options):
    """把「改文字 / 读文字」收成方法。"""

    def set_text(self, text: Any) -> Any:
        """改显示文字，等价于 ``configure(text=...)``，返回控件自己。

        参数:
            text: 任意值，内部 ``str()`` 一次。
        """
        self.configure(text=str(text))
        return self

    def get_text(self) -> str:
        """读回当前文字；控件没有 ``text`` 选项时返回空字符串。"""
        try:
            return str(self.cget("text"))
        except Exception:  # noqa: BLE001 - 没有 text 选项
            return ""
