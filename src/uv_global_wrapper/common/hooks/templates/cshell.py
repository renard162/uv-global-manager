from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_cshell_hook_script() -> str:
    commands = " ".join(COMMANDS_DICT.values())
    venvs_path = path_as_posix(venvs_root_path(abs_path=False))

    return dedent(r"""
        alias uvg 'if ("!:1" == "activate" && "!:2" != "" && "!:2" != "-h" && "!:2" != "--help") then; eval `\uvg activate "\!:2" --hook cshell`; else; \uvg !\*; endif'
    """).strip()
