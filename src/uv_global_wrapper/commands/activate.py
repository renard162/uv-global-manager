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

    parser = subparsers.add_parser("activate")

    parser.add_argument("name")

    parser.set_defaults(func=activate_run)


def activate_run(args: argparse.Namespace):
    parser: argparse.ArgumentParser = args.parser

    if args.name is None:
        parser.print_help()
        return

    _, shell_family = get_parent_shell()
    script_extension = get_script_extension(shell_family)
    activation_script = venv_script_path(args.name) / f"activate{script_extension}"

    if not activation_script.is_file():
        raise FileNotFoundError(
            f"Virtual environment '{args.name}' was not found or is corrupted."
        )

    os_name = os.name
    if os_name == "nt" and shell_family == "posix":
        activation_script = path_as_windows_bash(activation_script)
    elif os_name == "nt":
        activation_script = path_as_windows(activation_script)
    else:
        activation_script = path_as_posix(activation_script)

    print(activation_script)
