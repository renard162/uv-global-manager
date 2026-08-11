from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
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
    hook_script_path,
    repository_path,
    resources_path,
    venvs_root_path,
)
from ..common.utils import get_parent_shell


@dataclass
class InstallationPlan:
    profile_path: Path
    action: str
    backup: bool = False


def register(subparsers):
    parser = subparsers.add_parser("setup", allow_abbrev=False)

    install_group = parser.add_mutually_exclusive_group()

    install_group.add_argument(
        "--install",
        nargs="?",
        metavar="PROFILE",
    )
    install_group.add_argument(
        "--reinstall",
        nargs="?",
        metavar="PROFILE",
    )

    parser.set_defaults(func=setup_run, parser=parser)


def setup_run(args: argparse.Namespace):
    if args.install is None and args.reinstall is None:
        args.parser.print_help()
        return

    shell_name, shell_family = get_parent_shell()

    if args.install is not None:
        install(
            profile=args.install,
            shell_name=shell_name,
            shell_family=shell_family,
            reinstall=False,
        )
        return

    if args.reinstall is not None:
        install(
            profile=args.reinstall,
            shell_name=shell_name,
            shell_family=shell_family,
            reinstall=True,
        )
        return

    if shell_family == "cmd":
        return setup_cmd_without_profile()

    raise ValueError("A profile must be specified with --install or --reinstall.")


def install(
    *,
    profile: str | None,
    shell_name: str,
    shell_family: str,
    reinstall: bool,
):
    if profile is None:
        if shell_family == "cmd":
            return setup_cmd_without_profile()

        raise ValueError("A profile must be specified with --install or --reinstall.")

    profile_path = Path(profile).expanduser().resolve()

    plan = build_installation_plan(
        profile_path=profile_path,
        shell_family=shell_family,
        reinstall=reinstall,
    )

    print_installation_plan(
        plan=plan,
        shell_name=shell_name,
        shell_family=shell_family,
        reinstall=reinstall,
    )

    if not confirm_installation():
        print("Installation aborted.")
        return

    generate_hook_script(shell_family=shell_family)

    execute_installation_plan(
        plan=plan,
        shell_family=shell_family,
    )


def build_installation_plan(
    *,
    profile_path: Path,
    shell_family: str,
    reinstall: bool,
) -> InstallationPlan:
    if not profile_path.exists():
        raise FileNotFoundError(f'The profile "{profile_path}" does not exist.')

    if profile_path.is_dir():
        launcher_path = profile_path / get_hook_launcher_script_name(
            shell_family=shell_family
        )

        if reinstall:
            action = "overwrite"
        elif launcher_path.exists():
            action = "skip"
        else:
            action = "create"

        return InstallationPlan(
            profile_path=launcher_path,
            action=action,
        )

    if profile_path.is_file():
        block = find_hook_launcher_code_block(
            script_path=profile_path,
            shell_family=shell_family,
        )

        if block is None:
            action = "insert"
        elif reinstall:
            action = "replace"
        else:
            action = "skip"

        return InstallationPlan(
            profile_path=profile_path,
            action=action,
            backup=action in {"insert", "replace"},
        )

    raise ValueError(f'The profile "{profile_path}" is neither a file nor a directory.')


def print_installation_plan(
    *,
    plan: InstallationPlan,
    shell_name: str,
    shell_family: str,
    reinstall: bool,
):
    print()
    print("The following changes will be made:")
    print()
    print(f"Shell: {shell_name} ({shell_family})")
    print()

    print_installation_action(plan)
    print_installation_backup(plan)

    print()


def print_installation_action(plan: InstallationPlan):
    if plan.action == "create":
        print("Create file:")
        print(f"  + {plan.profile_path}")
        return

    if plan.action == "overwrite":
        print("Overwrite file:")
        print(f"  ~ {plan.profile_path}")
        return

    if plan.action == "insert":
        print("Edit file:")
        print(f"  ~ {plan.profile_path}")
        print("  Insert the hook launcher call at the end of the file.")
        return

    if plan.action == "replace":
        print("Edit file:")
        print(f"  ~ {plan.profile_path}")
        print("  Remove the existing hook launcher block.")
        print("  Insert the hook launcher call at the end of the file.")
        return

    if plan.action == "skip":
        print("No changes required:")
        print(f"  = {plan.profile_path}")
        return

    raise RuntimeError(f"Unknown installation action: {plan.action}")


def print_installation_backup(plan: InstallationPlan):
    if not plan.backup:
        return

    print()
    print("Backup:")
    print(f"  A backup of {plan.profile_path} will be created before editing.")


def confirm_installation() -> bool:
    answer = input("Continue with the installation? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def execute_installation_plan(
    *,
    plan: InstallationPlan,
    shell_family: str,
):
    if plan.action == "skip":
        return

    if plan.backup:
        backup_file(path=plan.profile_path)

    if plan.action in {"create", "overwrite"}:
        generate_hook_launcher_script(
            folder_path=plan.profile_path.parent,
            shell_family=shell_family,
        )
        return

    if plan.action == "insert":
        insert_hook_launcher_code_block(
            script_path=plan.profile_path,
            shell_family=shell_family,
        )
        return

    if plan.action == "replace":
        block = find_hook_launcher_code_block(
            script_path=plan.profile_path,
            shell_family=shell_family,
        )

        if block is None:
            raise RuntimeError(
                f'The hook launcher block in "{plan.profile_path}" '
                "was removed before installation."
            )

        remove_hook_launcher_code_block(
            script_path=plan.profile_path,
            block_positions=block,
        )

        insert_hook_launcher_code_block(
            script_path=plan.profile_path,
            shell_family=shell_family,
        )
        return

    raise RuntimeError(f"Unknown installation action: {plan.action}")


def setup_cmd_without_profile():
    raise NotImplementedError(
        "CMD installation without a profile is not implemented yet."
    )


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
