"""pytest 公共夹具。

ctk-kit 是纯 Tk 控件库，几乎所有行为都要在真实 Tk 窗口里才成立，所以测试
统一用「真窗口 + 全透明」的方式跑：窗口照常映射、几何尺寸和事件都正常，
但 alpha=0 用户看不到，不会一串窗口在屏幕上乱闪。

没有图形环境（例如无头 Linux CI）时，``root`` 会 skip 而不是报错。
"""

from __future__ import annotations

import time

import customtkinter as ctk
import pytest


@pytest.fixture(autouse=True)
def _light_appearance():
    """每个用例从浅色开始，避免主题状态串到下一个用例。"""
    ctk.set_appearance_mode("Light")
    yield
    ctk.set_appearance_mode("Light")


@pytest.fixture(autouse=True)
def _fresh_measurers():
    """清空按钮的文字测量缓存。

    ``tkfont.Font`` 绑在创建它的那个 Tk 解释器上，而测试每个用例都换窗口；
    缓存跨用例复用就会去测量一个已经销毁的解释器。真实应用只有一个根窗口，
    不会遇到这个问题，测试里按用例隔离即可。
    """
    from ctk_kit import buttons

    buttons._MEASURERS.clear()
    yield
    buttons._MEASURERS.clear()


@pytest.fixture()
def root():
    """一个映射到屏幕、但完全透明的 CTk 根窗口。"""
    last_error = None
    for _ in range(3):
        try:
            window = ctk.CTk()
            break
        except Exception as exc:  # noqa: BLE001 - 无 display / Tcl 初始化失败
            last_error = exc
            time.sleep(0.1)
    else:
        pytest.skip(f"当前环境无法创建 Tk 窗口：{last_error}")

    window.geometry("960x720+0+0")
    try:
        window.attributes("-alpha", 0.0)
    except Exception:  # noqa: BLE001 - 少数 Tk 构建不支持 alpha
        window.withdraw()
    window.update()
    try:
        yield window
    finally:
        window.destroy()


@pytest.fixture()
def settle():
    """跑满一段真实时间，让 ``after()`` 定时器和布局回调落地。"""

    def _settle(window, seconds: float = 0.25) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            window.update()
            time.sleep(0.01)

    return _settle
