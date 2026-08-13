from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_cshell_hook_script() -> str:
    commands = " ".join(COMMANDS_DICT.values())
    venvs_path = path_as_posix(venvs_root_path(abs_path=False))

    return dedent(
        f"""
        alias uve 'if ("!:1" == "activate" && "!:2" != "" && "!:2" != "-h" && "!:2" != "--help") then; eval `\\uve activate "\\!:2" --hook cshell`; else; \\uve !\\*; endif'

        if ($?tcsh) then
            complete uve \\
                'p/1/({commands})/' \\
                'n/activate/`find "$HOME/{venvs_path}" -mindepth 1 -maxdepth 1 -type d -exec basename {{}} \\\\;/`/' \\
                'n/delete/`find "$HOME/{venvs_path}" -mindepth 1 -maxdepth 1 -type d -exec basename {{}} \\\\;/`/'
        endif
        """
    ).strip()
