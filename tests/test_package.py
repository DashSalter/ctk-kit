"""发布相关的包级契约：版本号、公开导出、类型标记、示例脚本。"""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
import pytest

import ctk_kit
from ctk_kit import buttons, dropdown, inputs, layout, scroll_list, theme, tokens


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", ctk_kit.__version__)


def test_package_docstring_exists():
    assert ctk_kit.__doc__ and ctk_kit.__doc__.strip()


def test_all_has_no_duplicates():
    assert len(ctk_kit.__all__) == len(set(ctk_kit.__all__))


def test_every_export_exists():
    missing = [name for name in ctk_kit.__all__ if not hasattr(ctk_kit, name)]
    assert missing == []


def test_star_import_works():
    namespace = {}
    exec("from ctk_kit import *", namespace)  # noqa: S102 - 就是为了验证 __all__
    for name in ctk_kit.__all__:
        assert name in namespace


def test_public_classes_are_ctk_widgets():
    assert issubclass(ctk_kit.FlatButton, ctk.CTkButton)
    assert issubclass(ctk_kit.SoftButton, ctk_kit.FlatButton)
    assert issubclass(ctk_kit.DropField, ctk.CTkFrame)
    assert issubclass(ctk_kit.LazyList, tk.Frame)


def test_public_functions_are_callable():
    for name in (
        "primary_button",
        "soft_button",
        "danger_button",
        "card",
        "divider",
        "empty_hint",
        "field_label",
        "hint_label",
        "page_header",
        "scrollable",
        "section_title",
        "style_scrollable",
        "form_entry",
        "segmented",
        "switch",
        "toolbar_entry",
        "apply_appearance",
        "color_of",
        "is_dark",
        "repaint_native",
    ):
        assert callable(getattr(ctk_kit, name)), name


def test_submodules_are_importable():
    for module in (tokens, theme, buttons, inputs, dropdown, layout, scroll_list):
        assert module.__name__.startswith("ctk_kit.")


def test_py_typed_marker_is_shipped():
    assert Path(ctk_kit.__file__).with_name("py.typed").is_file()


def test_showcase_example_is_shipped_in_repo():
    showcase = Path(__file__).resolve().parents[1] / "examples" / "showcase.py"
    assert showcase.is_file()


def test_installed_metadata_matches_version():
    from importlib.metadata import PackageNotFoundError, version

    try:
        installed = version("ctk-kit")
    except PackageNotFoundError:
        pytest.skip("当前环境没有以 ctk-kit 的名字安装（仅源码可导入）")
    assert installed == ctk_kit.__version__
