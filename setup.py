from __future__ import annotations

from setuptools import setup
import sys

for arg in sys.argv:
    if arg in ("upload", "register"):
        print("This setup is not designed to be uploaded or registered.")
        sys.exit(-1)

_dependency_groups = {
    "user": ["black", "rich", "rich-click", "typing-extensions", "ast-comments"],
}

setup(
    name="pyfo-formatter",
    version="0.9.8",
    author="OSi",
    author_email="ondrej.sienczak@gmail.com",
    url="https://github.com/ondiiik/pyfo",
    packages=[
        "pyfo_formatter",
        "pyfo_formatter.code_parser",
        "pyfo_formatter.console",
        "pyfo_formatter.rules_checker",
    ],
    python_requires=">=3.12",
    # install_requires=["pyfo-formater[user]"],
    extras_require=_dependency_groups,
    entry_points={
        "console_scripts": [
            "pyfo-formatter=pyfo_formatter.__main__:main",
        ],
    },
    zip_safe=False,
)
