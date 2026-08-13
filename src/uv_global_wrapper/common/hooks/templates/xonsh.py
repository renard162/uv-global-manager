from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_xonsh_hook_script() -> str:
    commands = repr(tuple(COMMANDS_DICT.values()))
    venvs_path = path_as_posix(venvs_root_path(abs_path=False))

    return dedent(f"""
        import os
        import subprocess
        import sys

        _uve_commands = {commands}
        _uve_venvs_root = os.path.expanduser("~/{venvs_path}")

        def _uve_complete(command, alias):
            if command.arg_index == 1:
                prefix = command.prefix

                return {{
                    option
                    for option in _uve_commands
                    if option.startswith(prefix)
                }}

            if command.arg_index != 2:
                return None

            subcommand = command.args[1].value

            if subcommand not in ("activate", "delete"):
                return None

            if not os.path.isdir(_uve_venvs_root):
                return set()

            prefix = command.prefix

            return {{
                entry.name
                for entry in os.scandir(_uve_venvs_root)
                if entry.is_dir() and entry.name.startswith(prefix)
            }}

        def _uve(args):
            if (
                len(args) >= 2
                and args[0] == "activate"
                and args[1] not in ("-h", "--help")
            ):
                result = subprocess.run(
                    ["uve", "activate", *args[1:], "--hook", "xonsh"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(result.stderr, end="", file=sys.stderr)
                    return result.returncode

                __xonsh__.execer.exec(result.stdout)
                return 0

            return subprocess.run(["uve", *args]).returncode

        _uve.xonsh_complete = _uve_complete
        __xonsh__.aliases["uve"] = _uve
    """).strip()
