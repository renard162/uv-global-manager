from __future__ import annotations

import argparse
import os

from ..utils import (
    get_parent_shell,
    get_script_extension,
    path_as_posix,
    path_as_windows,
    path_as_windows_bash,
    venv_script_path,
)


def register(subparsers):
    parser = subparsers.add_parser(
        "activate",
        help="Activate a global virtual environment.",
        description="Activates a global virtual environment.",
    )

    parser.add_argument(
        "name",
        nargs="?",
        help="Name of the virtual environment to activate.",
    )

    parser.set_defaults(
        func=activate_run,
        parser=parser,
    )


def activate_run(args: argparse.Namespace):
    if (args.name is None) or (args.name == ""):
        args.parser.print_help()
        return

    _, shell_family = get_parent_shell()
    script_extension = get_script_extension(shell_family)
    activation_script = venv_script_path(args.name) / f"activate{script_extension}"

    if not activation_script.is_file():
        raise FileNotFoundError(
            f"Virtual environment '{args.name}' was not found or is corrupted."
        )

    if (os.name == "nt") and (shell_family == "posix"):
        script_path = path_as_windows_bash(activation_script)
    elif os.name == "nt":
        script_path = path_as_windows(activation_script)
    else:
        script_path = path_as_posix(activation_script)

    activation_commands_dict = {
        "posix": f'source "{script_path}"',
        "c_shell": f'source "{script_path}"',
        "fish": f'source "{script_path}"',
        "powershell": f'. "{script_path}"',
        "cmd": f'call "{script_path}"',
        "nushell": f'source "{script_path}"',
        "xonsh": f'source "{script_path}"',
    }

    activation_command = activation_commands_dict[shell_family]

    # Printed command is executed by hook
    print(activation_command)
