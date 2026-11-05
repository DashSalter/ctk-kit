"""把 ``_src/`` 里的核心模块编译成稳定 ABI（abi3）的 ``.pyd``。

    python -m tools.build_core          # 编译并放到 ctk_kit/
    python -m tools.build_core --copy   # 只把源码拷过去（本地开发用）

``_src/`` 是私有的：源码留在本地、不提交；仓库里只有 ``ctk_kit/*.pyd`` 和
``ctk_kit/*.pyi``。用 ``Py_LIMITED_API`` 编译出来的 ``.pyd`` 不带 ``cp3xx``
后缀，Python 3.9 及以上都能加载。

编译需要 MSVC（VS 2022 的 Build Tools 即可），本地和 GitHub Actions 的
``windows-latest`` 都自带。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_src"
PKG = ROOT / "ctk_kit"

#: 要保护源码、编成二进制的模块。
MODULES = ("win32", "glass", "frost_layer")

#: 稳定 ABI 基线：3.9。想照顾更老的版本就把这里往下调。
LIMITED_API = "0x03090000"


def copy_sources() -> None:
    """开发模式：直接把源码拷进包目录，改一行就能跑，不用等编译。"""
    missing = [name for name in MODULES if not (SRC / f"{name}.py").exists()]
    if missing:
        raise SystemExit(f"_src/ 里缺少：{', '.join(missing)}")
    for name in MODULES:
        shutil.copy2(SRC / f"{name}.py", PKG / f"{name}.py")
    print(f"已复制 {len(MODULES)} 个模块到 ctk_kit/（这些 .py 已被 .gitignore 忽略）")


def build() -> int:
    """编译模式：Cython + abi3，产物是 ctk_kit/<name>.pyd。"""
    try:
        from Cython.Build import cythonize
        from setuptools import Extension, setup
    except ImportError as exc:  # pragma: no cover - 环境缺依赖
        raise SystemExit("需要 cython 和 setuptools：pip install cython") from exc

    missing = [name for name in MODULES if not (SRC / f"{name}.py").exists()]
    if missing:
        raise SystemExit(f"_src/ 里缺少：{', '.join(missing)}")

    extensions = [
        Extension(
            f"ctk_kit.{name}",
            [str(SRC / f"{name}.py")],
            define_macros=[("Py_LIMITED_API", LIMITED_API)],
            py_limited_api=True,
        )
        for name in MODULES
    ]

    # setup() 会去读 sys.argv，这里显式给参数，免得被 -m 的参数干扰。
    argv = sys.argv
    sys.argv = ["build_core", "build_ext", "--inplace"]
    try:
        setup(
            script_args=["build_ext", "--inplace"],
            ext_modules=cythonize(
                extensions, language_level=3, quiet=True, compiler_directives={"binding": True}
            ),
            options={"bdist_wheel": {"py_limited_api": "cp39"}},
        )
    finally:
        sys.argv = argv

    # Cython 会把中间 .c 留在包目录里，提交前清掉。
    for path in PKG.glob("*.c"):
        path.unlink(missing_ok=True)

    built = [PKG / f"{name}.pyd" for name in MODULES]
    for path in built:
        if not path.exists():
            raise SystemExit(f"没生成 {path.name}，检查上面的编译输出")
    print("编译完成：" + "、".join(p.name for p in built))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="编译 ctk_kit 核心模块")
    parser.add_argument("--copy", action="store_true", help="只复制源码，不编译")
    args = parser.parse_args()
    if args.copy:
        copy_sources()
        return 0
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
