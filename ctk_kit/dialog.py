"""对话框：信息 / 成功 / 警告 / 错误 / 确认 / 输入。

和提示浮层（:mod:`ctk_kit.notify`）不同，这里是**模态窗口**：弹出期间
主窗口点不了，必须点按钮、按 Esc 或关掉窗口才能继续。实现方式是普通
``Toplevel`` + ``transient`` + ``grab_set`` + ``wait_window``——和
ttkbootstrap 的对话框一个路子。刻意没用无边框窗口：``overrideredirect``
在 Windows 上 ``grab_set`` 不一定拦得住主窗口的输入，模态会失效。

常用的三种直接调函数：:

    from ctk_kit import alert, confirm, prompt

    alert(app, "已保存到 D:/backup", title="完成", level="success")

    if confirm(app, "删除这份备份？", level="warn", danger=True, ok="删除"):
        ...

    name = prompt(app, "给备份起个名字", value="backup-01")

需要更自由的排版时直接用 :class:`Dialog`：``buttons`` 自己给，
按下的按钮的 ``value`` 由 :meth:`Dialog.show` 返回。
"""

from __future__ import annotations

import contextlib
import sys
import tkinter as tk
from typing import Any, Optional, Sequence

import customtkinter as ctk
from PIL import Image, ImageDraw

from . import tokens as T
from .buttons import CTkButton
from .fonts import get_font
from .inputs import FormEntry
from .theme import color_of

__all__ = ["Dialog", "alert", "confirm", "prompt"]

#: 各层级用的主色。
_LEVEL_COLORS = {
    "info": T.COLOR_ACCENT,
    "success": T.COLOR_SUCCESS,
    "warn": T.COLOR_WARNING,
    "error": T.COLOR_ERROR,
}

#: 只用作 ``on_result`` 之类的空回调。
_NOOP = None


def _badge(level: str, size: int = 34):
    """画一枚圆形图标：底是层级色，上面一个白色符号。

    4 倍尺寸画完再缩放，圆边和符号才不会有 canvas 那种阶梯。
    返回 PIL 图；调用方用 ``CTkImage`` 包一层，HighDPI 下才能跟着缩放。
    """
    scale = 4
    side = size * scale
    color = color_of(_LEVEL_COLORS.get(level, T.COLOR_ACCENT))
    image = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.ellipse((0, 0, side - 1, side - 1), fill=color)

    white = "#ffffff"
    stroke = max(2, side // 12)
    cx = cy = side / 2

    if level == "success":
        # 对勾
        pen.line(
            (cx - side * 0.20, cy + side * 0.01, cx - side * 0.05, cy + side * 0.16),
            fill=white,
            width=stroke,
        )
        pen.line(
            (cx - side * 0.05, cy + side * 0.16, cx + side * 0.22, cy - side * 0.16),
            fill=white,
            width=stroke,
        )
    elif level == "error":
        # 叉
        arm = side * 0.18
        pen.line((cx - arm, cy - arm, cx + arm, cy + arm), fill=white, width=stroke)
        pen.line((cx - arm, cy + arm, cx + arm, cy - arm), fill=white, width=stroke)
    elif level == "warn":
        # 竖线 + 圆点
        pen.line((cx, cy - side * 0.20, cx, cy + side * 0.05), fill=white, width=stroke)
        pen.ellipse(
            (cx - stroke / 2, cy + side * 0.13, cx + stroke / 2, cy + side * 0.13 + stroke),
            fill=white,
        )
    else:
        # 信息：一个 i
        pen.ellipse(
            (cx - stroke / 2, cy - side * 0.21, cx + stroke / 2, cy - side * 0.21 + stroke),
            fill=white,
        )
        pen.line((cx, cy - side * 0.02, cx, cy + side * 0.19), fill=white, width=stroke)

    return image.resize((size, size), Image.LANCZOS)


def _round_corners(window: tk.Misc, radius: int = 12) -> None:
    """把无边框窗口裁成圆角（Windows）；别的平台什么都不做。"""
    with contextlib.suppress(Exception):
        if sys.platform != "win32":
            return
        import ctypes

        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        preference = ctypes.c_int(2)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(preference), ctypes.sizeof(preference)
        )
        if result == 0:
            return
        scaling = window.winfo_toplevel()._get_window_scaling()
        r = int(radius * 2 * scaling)
        region = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, window.winfo_width() + 1, window.winfo_height() + 1, r, r
        )
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)


class Dialog(ctk.CTkToplevel):
    """一个等待用户操作的卡片窗口。

    参数:
        master: 父容器；对话框会相对它的窗口居中。
        title: 标题；为空时只显示正文。
        message: 正文，会自动换行。
        detail: 正文下面的小字补充，可以放路径、影响范围这类信息。
        level: ``"info"`` / ``"success"`` / ``"warn"`` / ``"error"``，决定图标颜色。
        buttons: ``[(文字, 返回值), ...]``；默认只有一个「确定」。
            最后一个按钮是主按钮（强调色）。
        prompt: 给初始值就多显示一个输入框，:meth:`show` 返回输入的字符串。
        danger: 主按钮是否用危险色（删除、清空这类操作）。
        width: 对话框宽度（逻辑像素），默认 392。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str = "",
        message: str = "",
        detail: str = "",
        level: str = "info",
        buttons: Optional[Sequence[tuple]] = None,
        prompt: Optional[str] = None,
        danger: bool = False,
        width: int = 392,
    ) -> None:
        super().__init__(master)
        self.withdraw()
        # 用普通窗口而不是 overrideredirect：无边框窗口在 Windows 上
        # grab_set() 不一定拦得住主窗口的输入，模态会失效。这里按
        # 无边框卡片：没有系统标题栏，弹出来就是一块圆角面板。
        # 模态不能只靠 grab_set（无边框窗口在 Windows 上拦不住标题栏和滚轮），
        # 真正的做法是 show() 期间把父窗口置为 disabled。
        self.overrideredirect(True)
        self.configure(fg_color=T.COLOR_BORDER)
        self._parent_window = master.winfo_toplevel()

        self._result: Any = None
        self._buttons: list = list(buttons) if buttons else [("确定", True)]
        self._prompt = prompt
        self._entry: Optional[FormEntry] = None
        self._badge_source = _badge(level)
        self._photo = ctk.CTkImage(
            light_image=self._badge_source,
            dark_image=self._badge_source,
            size=(34, 34),
        )
        self._width = max(300, int(width))

        body = ctk.CTkFrame(
            self,
            fg_color=T.COLOR_CARD,
            corner_radius=T.RADIUS_MEDIUM - 1,
            border_width=0,
        )
        body.pack(fill="both", expand=True, padx=1, pady=1)

        head = ctk.CTkFrame(body, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(18, 0))

        icon = ctk.CTkLabel(
            head,
            text="",
            image=self._photo,
            width=34,
            fg_color="transparent",
        )
        icon.pack(side="left", padx=(0, 12))

        if title:
            heading = ctk.CTkLabel(
                head,
                text=title,
                anchor="w",
                font=get_font(T.FONT_CARD_TITLE),
                text_color=T.COLOR_TEXT,
                fg_color="transparent",
            )
            heading.pack(side="left", fill="x", expand=True)

        if message:
            text = ctk.CTkLabel(
                body,
                text=message,
                anchor="w",
                justify="left",
                wraplength=self._width - 86,
                font=get_font(T.FONT_BODY),
                text_color=T.COLOR_TEXT_SOFT if title else T.COLOR_TEXT,
                fg_color="transparent",
            )
            text.pack(fill="x", padx=18, pady=(12 if title else 0, 0))

        if detail:
            extra = ctk.CTkLabel(
                body,
                text=detail,
                anchor="w",
                justify="left",
                wraplength=self._width - 86,
                font=get_font(T.FONT_SMALL),
                text_color=T.COLOR_MUTED,
                fg_color="transparent",
            )
            extra.pack(fill="x", padx=18, pady=(8, 0))

        if prompt is not None:
            self._entry = FormEntry(body, placeholder="", height=36)
            self._entry.pack(fill="x", padx=18, pady=(14, 0))
            self._entry.insert(0, prompt)
            self._entry._entry.bind("<Return>", lambda _e: self._submit_prompt())

        footer = ctk.CTkFrame(body, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(18, 16))

        last = len(self._buttons) - 1
        for index in range(last, -1, -1):
            label, value = self._buttons[index]
            if index == last:
                background = T.COLOR_DANGER if danger else T.COLOR_ACCENT
                hover = T.COLOR_DANGER if danger else T.COLOR_ACCENT_HOVER
                foreground = T.COLOR_ACCENT_TEXT
            else:
                background = T.COLOR_SOFT
                hover = T.COLOR_SOFT_HOVER
                foreground = T.COLOR_TEXT
            button = CTkButton(
                footer,
                text=str(label),
                width=88,
                height=34,
                fg_color=background,
                hover_color=hover,
                text_color=foreground,
                command=lambda v=value: self._finish(v),
            )
            button.pack(side="right", padx=(8, 0))

        self.bind("<Escape>", lambda _e: self._finish(None))
        self.protocol("WM_DELETE_WINDOW", lambda: self._finish(None))

        self._wheel_bind = None
        self._wheel_bind_linux = None
        self._wheel_bind_linux5 = None
        self._move_bind = None

        self.update_idletasks()
        self._place_over(master)

    # ------------------------------------------------------------ 定位
    def _place_over(self, master: tk.Misc) -> None:
        """在父窗口中间摆好；父窗口不可用时退回屏幕中间。

        宽度固定成 ``width``，只让高度跟着内容走——几种对话框放在一起宽度一致，
        看起来才像同一个组件；文字换行由 ``wraplength`` 负责。

        最后把坐标夹进屏幕：父窗口被拖到屏幕外时，对话框仍然停在看得见的地方，
        不会跟着一起消失。
        """
        self.update_idletasks()
        width = self._width
        height = self.winfo_reqheight()
        # 记下来给 _reposition 用：拖动时每帧读 winfo_height 会被自己的
        # geometry 反复放大，必须固定在第一次算出的尺寸上
        self._frame_size = (width, height)
        try:
            parent = master.winfo_toplevel()
            left = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
            top = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        except tk.TclError:
            left = (self.winfo_screenwidth() - width) // 2
            top = (self.winfo_screenheight() - height) // 2
        # 夹进屏幕：窗口被拖到屏幕外时，对话框至少还能看见、能点
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        left = min(max(0, left), max(0, screen_w - width))
        top = min(max(0, top), max(0, screen_h - height))
        self.geometry(f"{width}x{height}+{left}+{top}")

    # ------------------------------------------------------------ 结果
    def _submit_prompt(self) -> None:
        """输入框里按回车：等同点主按钮。"""
        self._finish(self._buttons[-1][1])

    def _finish(self, value: Any) -> None:
        """记下返回值并关窗。"""
        if self._prompt is not None and self._entry is not None:
            if value == self._buttons[-1][1]:
                value = self._entry.get()
            else:
                value = None
        self._result = value
        with contextlib.suppress(tk.TclError):
            self.grab_release()
        self.destroy()

    def show(self) -> Any:
        """显示并等待用户操作，返回按下的按钮对应的值。

        关掉窗口或按 Esc 返回 ``None``；有输入框时返回输入的文字。

        模态靠三件事，而不是把父窗口整个禁用：

        - ``grab_set``：客户区的点击、键盘都进不来
        - 父窗口上临时绑 ``<MouseWheel>`` 并 ``return "break"``：滚轮被截住。
          单靠 grab 不行，CTk 的滚动区走的是 ``bind_all``，那条链不受 grab 管
        - 父窗口移动时重新居中：标题栏可以拖，对话框跟着走

        位置会被夹在屏幕内，父窗口拖到屏幕外时对话框仍然可见。
        """
        parent = self._parent_window
        self.deiconify()
        self.wait_visibility()
        _round_corners(self)
        # 无边框窗口不参与 WM 的层级管理：拖动主窗口时它会被压到下面，看起来像
        # 「消失了」。对话框本来就是模态，关掉之前一直置顶即可。
        with contextlib.suppress(tk.TclError):
            self.attributes("-topmost", True)
        self.grab_set()

        # 滚轮：拦在 toplevel 这一层，比 bind_all 早一步
        self._wheel_bind = parent.bind("<MouseWheel>", self._block_wheel, add="+")
        self._wheel_bind_linux = parent.bind("<Button-4>", self._block_wheel, add="+")
        self._wheel_bind_linux5 = parent.bind("<Button-5>", self._block_wheel, add="+")
        # 拖动 / 缩放窗口时跟着走
        self._move_bind = parent.bind("<Configure>", self._on_parent_configure, add="+")

        if self._entry is not None:
            self._entry.focus_set()
            self._entry._entry.icursor("end")
        else:
            self.focus_force()
        try:
            self.wait_window(self)
        finally:
            for event, bind_id in (
                ("<MouseWheel>", self._wheel_bind),
                ("<Button-4>", self._wheel_bind_linux),
                ("<Button-5>", self._wheel_bind_linux5),
                ("<Configure>", self._move_bind),
            ):
                with contextlib.suppress(tk.TclError):
                    parent.unbind(event, bind_id)
            with contextlib.suppress(tk.TclError):
                self.grab_release()
            with contextlib.suppress(tk.TclError):
                self.attributes("-topmost", False)
        return self._result

    def _block_wheel(self, _event: tk.Event) -> str:
        """截住滚轮：对话框打开时背景不该跟着滚。"""
        return "break"

    def _on_parent_configure(self, event: Optional[tk.Event] = None) -> None:
        """父窗口动了就立刻重新居中，拖窗口时对话框跟手走。

        ``<Configure>`` 绑在顶层窗口上会收到所有子控件冒泡上来的事件（滚动页面
        时每帧几十个），所以先按 ``event.widget`` 过滤掉。

        这里直接重排、不隔帧：Windows 上 Tk 处理 ``WM_MOVE`` 时是同步分发
        ``<Configure>`` 的，隔帧会退回主循环，拖动过程中就完全不跟手——
        DropField 的下拉面板能跟手，用的也是这个路子。
        """
        if event is not None:
            with contextlib.suppress(tk.TclError):
                if event.widget is not self._parent_window.winfo_toplevel():
                    return
        self._reposition()


    def _reposition(self) -> None:
        """重新居中；拖动时每帧都会走这里，所以不碰 ``update_idletasks``。

        尺寸已经定下来了（``_place_over`` 里算过），这里只用现成的高度和父窗口
        位置重算坐标，再夹进屏幕。
        """
        if not self.winfo_exists():
            return
        parent = self._parent_window.winfo_toplevel()
        width, height = getattr(
            self, "_frame_size", (self._width, max(120, self.winfo_reqheight()))
        )
        left = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        top = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        left = min(max(0, left), max(0, screen_w - width))
        top = min(max(0, top), max(0, screen_h - height))
        with contextlib.suppress(tk.TclError):
            self.geometry(f"{width}x{height}+{left}+{top}")


def alert(
    master: tk.Misc,
    message: str,
    *,
    title: str = "",
    level: str = "info",
    ok: str = "知道了",
    detail: str = "",
) -> None:
    """信息框：只有一个「知道了」。"""
    Dialog(
        master,
        title=title,
        message=message,
        detail=detail,
        level=level,
        buttons=[(ok, True)],
    ).show()


def confirm(
    master: tk.Misc,
    message: str,
    *,
    title: str = "",
    level: str = "warn",
    ok: str = "确定",
    cancel: str = "取消",
    detail: str = "",
    danger: bool = False,
) -> bool:
    """确认框：返回 ``True`` 表示点了 ``ok``。"""
    result = Dialog(
        master,
        title=title,
        message=message,
        detail=detail,
        level=level,
        buttons=[(cancel, False), (ok, True)],
        danger=danger,
    ).show()
    return bool(result)


def prompt(
    master: tk.Misc,
    message: str,
    *,
    title: str = "",
    value: str = "",
    ok: str = "确定",
    cancel: str = "取消",
    detail: str = "",
) -> Optional[str]:
    """输入框：返回输入的文字；点取消返回 ``None``。"""
    result = Dialog(
        master,
        title=title,
        message=message,
        detail=detail,
        level="info",
        buttons=[(cancel, False), (ok, True)],
        prompt=value,
    ).show()
    return result if isinstance(result, str) else None
