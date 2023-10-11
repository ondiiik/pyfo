from __future__ import annotations

from setuptools import setup
import sys

for arg in sys.argv:
    if arg in ("upload", "register"):
        print("This setup is not designed to be uploaded or registered.")
        sys.exit(-1)

_dependency_groups = {
    "user": ["black", "rich", "rich-click", "typing-extensions"],
}

setup(
    name="pyfo",
    version="0.9.8",
    author="OSi",
    author_email="ondrej.sienczak@gmail.com",
    url="https://github.com/ondiiik/pyfo",
    packages=[
        "pyfo",
        "pyfo.code_parser",
        "pyfo.console",
        "pyfo.rules_checker",
    ],
    python_requires=">=3.10",
    install_requires=["pyfo[user]"],
    extras_require=_dependency_groups,
    entry_points={
        "console_scripts": [
            "pyfo=pyfo.__main__:main",
        ],
    },
    zip_safe=False,
)
