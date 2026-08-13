from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_cshell_hook_script() -> str:
    return dedent(r"""
        alias uve 'if ("\!:1*" =~ "activate *" && "\!:1*" != "activate -h" && "\!:1*" != "activate --help") eval `\uve activate "\!:2*" --hook cshell`; if ("\!:1*" !~ "activate *" || "\!:1*" == "activate -h" || "\!:1*" == "activate --help") \uve \!*'
    """).strip()
