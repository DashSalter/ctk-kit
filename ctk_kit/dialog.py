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
import tkinter as tk
from typing import Any, Optional, Sequence

import customtkinter as ctk
from PIL import Image, ImageDraw

from . import tokens as T
from .buttons import CTkButton
from .fonts import get_font
from .inputs import FormEntry
from .theme import color_of, is_dark, set_titlebar_dark

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
        # ttkbootstrap 的做法——有标题栏、transient、grab_set。
        self.title(title or " ")
        self.transient(master.winfo_toplevel())
        self.resizable(False, False)
        self.configure(fg_color=T.COLOR_BG)

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

        if message:
            text = ctk.CTkLabel(
                body,
                text=message,
                anchor="w",
                justify="left",
                wraplength=self._width - 86,
                font=get_font(T.FONT_BODY),
                text_color=T.COLOR_TEXT,
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

        self.update_idletasks()
        self._place_over(master)

    # ------------------------------------------------------------ 定位
    def _place_over(self, master: tk.Misc) -> None:
        """在父窗口中间摆好；父窗口不可用时退回屏幕中间。

        宽度固定成 ``width``，只让高度跟着内容走——几种对话框放在一起宽度一致，
        看起来才像同一个组件；文字换行由 ``wraplength`` 负责。
        """
        self.update_idletasks()
        width = self._width
        height = self.winfo_reqheight()
        try:
            parent = master.winfo_toplevel()
            left = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
            top = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        except tk.TclError:
            left = (self.winfo_screenwidth() - width) // 2
            top = (self.winfo_screenheight() - height) // 2
        left = max(0, left)
        top = max(0, top)
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
        弹出期间 ``grab_set`` 会把所有输入都截到这个窗口上，主窗口点不了。
        """
        self.deiconify()
        self.wait_visibility()
        # 标题栏跟进外观：窗口真正 mapped 之后 DWM 才接管
        self.after(10, lambda: set_titlebar_dark(self, is_dark()))
        self.lift()
        self.grab_set()
        if self._entry is not None:
            self._entry.focus_set()
            self._entry._entry.icursor("end")
        else:
            self.focus_force()
        self.wait_window(self)
        return self._result


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
