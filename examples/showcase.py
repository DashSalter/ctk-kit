"""仓库里的示例入口，等价于 ``python -m ctk_kit.showcase``。

示例本体在 ``ctk_kit/showcase.py``，随 wheel 一起发布；装好包之后可以直接运行
``ctk-kit-showcase``。这个文件只是给 clone 下来、还没 pip install 的场景留个
快捷方式。
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ctk_kit.showcase import main

if __name__ == "__main__":
    sys.exit(main())
