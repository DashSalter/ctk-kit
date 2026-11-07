"""文件与文件夹选择：路径输入框、拖放取路径。

拖放依赖可选的 ``tkinterdnd2``（``pip install "ctk-kit[dnd]"``）。没装时
``PathField`` 仍能点按钮选择，``DropZone`` 会显示成不可拖的提示。
"""

from __future__ import annotations

import contextlib
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Any, Callable, Optional

import customtkinter as ctk

from . import tokens as T
from .buttons import SecondaryButton
from .fonts import get_font
from .sugar import Valuable
from .inputs import FormEntry

try:  # pragma: no cover - 取决于有没有装可选依赖
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover
    DND_FILES = None  # type: ignore[assignment]
    TkinterDnD = None  # type: ignore[assignment]

PathMode = str  # "file" | "folder"

_DND_ROOTS: dict = {}


def has_dnd() -> bool:
    """当前环境能不能拖放（装了 tkinterdnd2 才为真）。"""
    return TkinterDnD is not None


def pick_path(
    master: tk.Misc,
    *,
    mode: PathMode = "file",
    title: Optional[str] = None,
    initialdir: Optional[str] = None,
    filetypes: Optional[list] = None,
) -> str:
    """弹系统对话框选文件或文件夹，取消返回空字符串。"""
    if mode == "folder":
        return filedialog.askdirectory(
            parent=master,
            title=title or "选择文件夹",
            initialdir=initialdir,
            mustexist=True,
        )
    return filedialog.askopenfilename(
        parent=master,
        title=title or "选择文件",
        initialdir=initialdir,
        filetypes=filetypes or [("所有文件", "*.*")],
    )


def _ensure_dnd(root: tk.Misc) -> bool:
    """在给定 Tk 根上加载一次 tkdnd 扩展，返回是否可用。"""
    if TkinterDnD is None:
        return False
    key = str(root)
    if key in _DND_ROOTS:
        return _DND_ROOTS[key]
    ok = True
    try:
        TkinterDnD._require(root)
    except Exception:
        ok = False
    _DND_ROOTS[key] = ok
    return ok


def _first_path(widget: tk.Misc, data: str) -> str:
    """tkdnd 给的是 Tcl 列表字符串，取第一个条目。"""
    try:
        items = widget.tk.splitlist(data)
    except tk.TclError:
        items = [data]
    return str(items[0]) if items else ""


def _drop_targets(widget: tk.Misc) -> list:
    """CTk 控件的可见部分是内部 canvas，只注册外层收不到 drop。"""
    targets = [widget]
    for name in ("_canvas", "_parent_frame", "_entry", "_textbox"):
        inner = getattr(widget, name, None)
        if inner is not None and hasattr(inner, "winfo_id"):
            targets.append(inner)
    return targets


def register_drop(widget: tk.Misc, on_path: Callable[[str], None]) -> bool:
    """让控件接住拖进来的文件/文件夹，成功返回 True。"""
    root = widget.winfo_toplevel()
    if not _ensure_dnd(root):
        return False

    def handler(event: Any) -> str:
        """拖放回调：取第一个路径交给 ``on_path``，返回拖放动作。"""
        path = _first_path(widget, event.data)
        if path:
            on_path(path)
        return getattr(event, "action", "copy")

    registered = False
    for target in _drop_targets(widget):
        try:
            target.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
            target.dnd_bind("<<Drop>>", handler)  # type: ignore[attr-defined]
        except Exception:
            continue
        registered = True
    return registered


class PathField(Valuable, ctk.CTkFrame):
    """输入框 + 浏览按钮，选好路径后直接覆盖输入框内容。

    ``mode="file"`` 选文件，``mode="folder"`` 选文件夹；``accept_drop=True``
    时还可以把文件/文件夹拖到输入框里。
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        mode: PathMode = "file",
        placeholder: str = "",
        height: int = 38,
        button_text: str = "浏览",
        title: Optional[str] = None,
        on_change: Optional[Callable[[str], None]] = None,
        accept_drop: bool = True,
        readonly: bool = False,
        **kwargs: Any,
    ) -> None:
        """建路径输入框和浏览按钮；``accept_drop`` 为真时再挂拖放。"""
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._mode = mode
        self._title = title
        self._on_change = on_change
        self._readonly = bool(readonly)

        self.entry = FormEntry(self, placeholder=placeholder, height=height)
        self.entry.pack(side="left", fill="x", expand=True)
        self.button = SecondaryButton(self, button_text, self.browse, width=64, height=height)
        self.button.pack(side="left", padx=(8, 0))

        self.entry.bind("<KeyRelease>", lambda _e: self._changed(), add="+")
        self.entry.bind("<FocusOut>", lambda _e: self._changed(), add="+")
        self.droppable = False
        if accept_drop:
            self.droppable = register_drop(self.entry, self._dropped)
        if self._readonly:
            self._apply_readonly()

    # --- 对外 ---
    def get(self) -> str:
        """当前输入框里的路径。"""
        return self.entry.get()

    def set_readonly(self, flag: bool = True) -> "PathField":
        """开关只读：只读时不能改内容，也不能点「浏览」。"""
        self._readonly = bool(flag)
        self._apply_readonly()
        return self

    def is_readonly(self) -> bool:
        """当前是否只读。"""
        return bool(getattr(self, "_readonly", False))

    def _apply_readonly(self) -> None:
        """只读时输入框拒收键盘，浏览按钮置灰。"""
        try:
            self.entry.configure(
                state="readonly" if self.is_readonly() else "normal"
            )
            self.button.configure(
                state="disabled" if self.is_readonly() else "normal"
            )
        except (tk.TclError, ValueError):
            return

    def set(self, path: str) -> None:
        """覆盖输入框内容并触发 ``on_change``。"""
        readonly = self.is_readonly()
        if readonly:
            with contextlib.suppress(Exception):
                self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        if path:
            self.entry.insert(0, path)
        if readonly:
            with contextlib.suppress(Exception):
                self.entry.configure(state="readonly")
        self._changed()

    def clear(self) -> None:
        """清空路径，等价于 ``set("")``（会触发 ``on_change``）。"""
        self.set("")

    def browse(self) -> str:
        """弹对话框；选中就把路径写进输入框并返回，取消返回空串。"""
        if self.is_readonly():
            return ""
        current = self.get()
        picked = pick_path(
            self,
            mode=self._mode,
            title=self._title,
            initialdir=current or None,
        )
        if picked:
            self.set(picked)
        return picked

    def _dropped(self, path: str) -> None:
        """拖放回调：直接把路径写进输入框；只读时忽略。"""
        if self.is_readonly():
            return
        self.set(path)

    def _changed(self) -> None:
        """输入内容变了：把最新值交给 ``on_change``。"""
        if self._on_change is not None:
            self._on_change(self.get())


class DropZone(ctk.CTkFrame):
    """把文件或文件夹拖进来的区域，松手后回调路径。

    ``mode="any"`` 文件与文件夹都收，``"file"`` / ``"folder"`` 只收对应类型。
    """

    def __init__(
        self,
        master: tk.Misc,
        on_path: Callable[[str], None],
        *,
        mode: PathMode = "any",
        height: int = 96,
        text: str = "把文件或文件夹拖到这里",
        hint: str = "",
        **kwargs: Any,
    ) -> None:
        """建拖放区；系统不支持拖放时显示安装提示。"""
        kwargs.setdefault("fg_color", T.COLOR_SOFT)
        kwargs.setdefault("corner_radius", T.RADIUS_MEDIUM)
        super().__init__(master, height=height, **kwargs)
        self._mode = mode
        self._on_path = on_path

        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=get_font(T.FONT_SMALL),
            text_color=T.COLOR_MUTED,
        )
        self.label.pack(expand=True, side="top", pady=(14, 0))
        self.hint = ctk.CTkLabel(
            self,
            text=hint,
            font=get_font(T.FONT_TINY),
            text_color=T.COLOR_FAINT,
        )
        self.hint.pack(side="top", pady=(2, 14))
        if not hint:
            self.hint.pack_forget()
        self.pack_propagate(False)

        self.droppable = self._setup_drop()
        if self.droppable:
            self.label.configure(text=text)
        else:
            self.label.configure(
                text="拖放需要 tkinterdnd2：pip install \"ctk-kit[dnd]\"",
                text_color=T.COLOR_FAINT,
            )

    def _setup_drop(self) -> bool:
        """给内部目标挂拖放事件；返回是否至少挂上一个。"""
        root = self.winfo_toplevel()
        if not _ensure_dnd(root):
            return False

        def on_drop(event: Any) -> str:
            """松手回调：取消高亮，路径合法就交给 ``_dropped``。"""
            self._highlight(False)
            path = _first_path(self, event.data)
            if path:
                self._dropped(path)
            return getattr(event, "action", "copy")

        registered = False
        for target in _drop_targets(self):
            try:
                target.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
                target.dnd_bind("<<Drop>>", on_drop)  # type: ignore[attr-defined]
                target.dnd_bind("<<DropEnter>>", lambda _e: self._highlight(True))  # type: ignore[attr-defined]
                target.dnd_bind("<<DropLeave>>", lambda _e: self._highlight(False))  # type: ignore[attr-defined]
            except Exception:
                continue
            registered = True
        return registered

    def _highlight(self, active: bool) -> None:
        """拖动经过时换高亮底色，离开时恢复。"""
        self.configure(fg_color=T.COLOR_HOVER_FAINT if active else T.COLOR_SOFT)

    def _dropped(self, path: str) -> None:
        """按 ``mode`` 过滤路径后交给 ``on_path``。"""
        self._highlight(False)
        try:
            is_dir = Path(path).is_dir()
        except OSError:
            is_dir = False
        if self._mode == "file" and is_dir:
            return
        if self._mode == "folder" and not is_dir:
            return
        self._on_path(path)
