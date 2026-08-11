from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ..common.hooks.generator import (
    find_hook_launcher_code_block,
    generate_hook_launcher_script,
    generate_hook_script,
    get_hook_launcher_script_name,
    insert_hook_launcher_code_block,
    remove_hook_launcher_code_block,
)
from ..common.paths import (
    repository_path,
    resources_path,
    venvs_root_path,
)
from ..common.utils import get_parent_shell


def register(subparsers):

    parser = subparsers.add_parser("setup", allow_abbrev=False)

    parser.set_defaults(func=setup_run, parser=parser)


def setup_run(args: argparse.Namespace):
    if args.name is None:
        args.parser.print_help()
        return


def backup_file(path: Path) -> str | None:
    if not path.is_file():
        return

    backup_files = list(path.parent.glob(f"{path.name}.bak*"))

    if not backup_files:
        backup_path = path.with_name(f"{path.name}.bak")
    else:
        backup_files.sort(key=lambda bck: bck.suffix)
        suffix = backup_files[-1].suffix.removeprefix(".bak")

        if suffix.isdigit():
            suffix = str(int(suffix) + 1)
        else:
            suffix += "0"

        backup_path = path.with_name(f"{path.name}.bak{suffix}")

    shutil.copy2(path, backup_path)
    return backup_path.name
