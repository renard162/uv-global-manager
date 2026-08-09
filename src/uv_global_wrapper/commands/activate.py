from __future__ import annotations

import argparse
from pathlib import Path

from shellingham import ShellDetectionFailure

from ..utils import (
    get_parent_shell,
    path_as_posix,
    path_as_windows,
    print_warning,
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

    parser.add_argument(
        "--hook",
        action="store_true",
        help=argparse.SUPPRESS,
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
    ext = get_activation_script_extension(shell_family)
    abs_activation_script = venv_script_path(args.name) / f"activate{ext}"

    if not abs_activation_script.is_file():
        raise FileNotFoundError(
            f"Virtual environment '{args.name}' or activation script '{abs_activation_script.name}' does not exist."
        )

    activation_script = abs_activation_script.relative_to(Path.home())
    if shell_family in ("cmd", "powershell"):
        script_path = path_as_windows(activation_script)
    else:
        script_path = path_as_posix(activation_script)

    activation_commands_dict = {
        "posix": f'source "$HOME/{script_path}"',
        "cshell": f'source "$HOME/{script_path}"',
        "fish": f'source "$HOME/{script_path}"',
        "powershell": f'. "$HOME\\{script_path}"',
        "cmd": f'call "%USERPROFILE%\\{script_path}"',
        "nushell": f'overlay use ($nu.home-dir | path join "{script_path}")',
        "xonsh": f'source "~/{script_path}"',
    }

    if not args.hook:
        print_warning(
            "The shell hook is not installed.\n"
            "You may run 'uvg setup' for instructions on installing the shell hook.\n"
            "Copy and paste the generated command to activate the virtual environment manually.\n"
        )

    # The printed command is executed by the hook
    activation_command = activation_commands_dict[shell_family]
    print(activation_command)


def get_activation_script_extension(shell_family: str) -> str:
    extension_dict = {
        "posix": "",
        "cshell": ".csh",
        "fish": ".fish",
        "powershell": ".ps1",
        "cmd": ".bat",
        "nushell": ".nu",
        "xonsh": ".xsh",
    }
    extension = extension_dict.get(shell_family, None)

    if extension is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return extension
