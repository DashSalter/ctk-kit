"""打包入口。

这里只做一件事：告诉 setuptools 这个包带二进制（``ctk_kit/core/*.pyd``）。

不声明的话，``bdist_wheel`` 会以为它是纯 Python 包，打出
``ctk_kit-0.9.2-py3-none-any.whl``——``any`` 意味着 Linux / macOS 也会装，
装完 import 才发现没有匹配的 ``.pyd``。配合 ``setup.cfg`` 的
``py_limited_api = cp39``，产物会变成 ``cp39-abi3-win_amd64``，平台不对的
机器在 pip 阶段就被挡掉。
"""

from setuptools import setup
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    """带编译产物的发行版：强制生成平台相关的 wheel。"""

    def has_ext_modules(self) -> bool:  # noqa: D102 - setuptools 的钩子
        return True


if __name__ == "__main__":
    setup(distclass=BinaryDistribution)
