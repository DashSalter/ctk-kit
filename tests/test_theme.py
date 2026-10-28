"""外观工具测试：取色、切换、原生控件重绘。"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ctk_kit import tokens as T
from ctk_kit.theme import apply_appearance, color_of, is_dark, repaint_native


def test_is_dark_follows_appearance_mode():
    ctk.set_appearance_mode("Light")
    assert is_dark() is False
    ctk.set_appearance_mode("Dark")
    assert is_dark() is True


def test_color_of_picks_tone_for_current_mode():
    pair = ("#111111", "#eeeeee")
    ctk.set_appearance_mode("Light")
    assert color_of(pair) == "#111111"
    ctk.set_appearance_mode("Dark")
    assert color_of(pair) == "#eeeeee"


def test_color_of_accepts_list():
    assert color_of(["#010203", "#040506"]) == "#010203"


def test_color_of_passes_plain_string_through():
    assert color_of("#123456") == "#123456"
    assert color_of("transparent") == "transparent"


def test_color_of_real_token():
    assert color_of(T.COLOR_ACCENT) == T.COLOR_ACCENT[0]


def test_apply_appearance_light_and_dark():
    apply_appearance("light")
    assert ctk.get_appearance_mode() == "Light"
    apply_appearance("dark")
    assert ctk.get_appearance_mode() == "Dark"


def test_apply_appearance_system_stays_valid():
    # 文档里写着接受 system，实现上除 light 之外一律落到 Dark；
    # 这里只锁「不炸、结果合法」，系统跟随本身交给 CTk 处理。
    apply_appearance("system")
    assert ctk.get_appearance_mode() in {"Light", "Dark"}


def test_apply_appearance_is_case_sensitive_for_light():
    # 现状：只有全小写的 "light" 会切到浅色，其余写法的语义需调用方自己保证。
    apply_appearance("LIGHT")
    assert ctk.get_appearance_mode() == "Dark"
    apply_appearance("light")


def test_repaint_native_changes_background(root):
    frame = tk.Frame(root, bg="#000000")
    frame.pack()
    repaint_native(frame, "#f0f0f0")
    root.update_idletasks()
    assert frame.cget("bg") == "#f0f0f0"


def test_repaint_native_ignores_destroyed_widget(root):
    frame = tk.Frame(root)
    frame.destroy()
    # 控件已经没了也不该抛：LazyList 在主题切换时会碰到这种时序
    repaint_native(frame, "#ffffff")


def test_repaint_native_works_on_any_widget(root):
    label = tk.Label(root, text="hi", bg="#000000")
    repaint_native(label, "#abcdef")
    root.update_idletasks()
    assert label.cget("bg") == "#abcdef"


def test_repaint_native_does_not_break_ctk_widget(root):
    frame = ctk.CTkFrame(root)
    repaint_native(frame, "#123456")  # 不抛即可，CTk 控件自己不认这个选项
