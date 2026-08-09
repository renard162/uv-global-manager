from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from ..utils import venvs_root_path


def register(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser(
        "delete",
        help="Remove a global virtual environment.",
        description="Deletes a global virtual environment.",
    )

    parser.add_argument(
        "name",
        nargs="?",
        help="Name of the virtual environment to delete.",
    )

    parser.set_defaults(func=delete_run, parser=parser)


def delete_run(args: argparse.Namespace):
    if args.name is None:
        args.parser.print_help()
        return

    env_path = venvs_root_path() / args.name

    if not env_path.is_dir():
        raise RuntimeError(f'Virtual environment "{args.name}" does not exist.')

    active_env = os.environ.get("VIRTUAL_ENV")
    if active_env and Path(active_env).resolve() == env_path.resolve():
        raise RuntimeError(f'Virtual environment "{args.name}" is currently active.')

    shutil.rmtree(env_path)

    print(f'Virtual environment "{args.name}" deleted successfully.')
