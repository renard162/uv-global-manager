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
        rf"""
        alias uve 'if ("\!:1*" =~ "activate *" && "\!:1*" != "activate -h" && "\!:1*" != "activate --help") eval `\uve activate "\!:2*" --hook cshell`; if ("\!:1*" !~ "activate *" || "\!:1*" == "activate -h" || "\!:1*" == "activate --help") \uve \!*'

        if ($?tcsh) then
            complete uve \
                'p/1/({commands})/' \
                'n@activate@`find "$HOME/{venvs_path}" -mindepth 1 -maxdepth 1 -type d -printf "%f\n"`@' \
                'n@delete@`find "$HOME/{venvs_path}" -mindepth 1 -maxdepth 1 -type d -printf "%f\n"`@'
        endif
        """
    ).strip()
