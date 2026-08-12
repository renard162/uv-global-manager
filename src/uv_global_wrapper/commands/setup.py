from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..common.hooks.generator_reg import (
    add_hook_launcher_to_autorun_reg,
    backup_autorun_win_reg,
    find_hook_launcher_win_reg,
    remove_hook_launcher_from_autorun_reg,
)
from ..common.hooks.generator_script import (
    backup_file,
    find_hook_launcher_code_block,
    generate_hook_launcher_script,
    generate_hook_script,
    get_hook_launcher_script_name,
    insert_hook_launcher_code_block,
    remove_hook_launcher_code_block,
)
from ..common.hooks.renders import render_shell_hook_call
from ..common.paths import (
    hook_script_path,
    repository_path,
    resources_path,
    venvs_root_path,
)
from ..common.utils import get_parent_shell


@dataclass
class InstallationPlan:
    profile_path: Path | None
    action: str
    win_reg_edit: bool
    backup: bool = False


def register(subparsers):
    parser = subparsers.add_parser("setup", allow_abbrev=False)

    install_group = parser.add_mutually_exclusive_group()

    install_group.add_argument(
        "--install",
        nargs="?",
        default=False,
        metavar="PROFILE",
    )
    install_group.add_argument(
        "--reinstall",
        nargs="?",
        default=False,
        metavar="PROFILE",
    )

    parser.set_defaults(func=setup_run, parser=parser)


def setup_run(args: argparse.Namespace):
    if args.install is False and args.reinstall is False:
        args.parser.print_help()
        return

    shell_name, shell_family = get_parent_shell()

    if args.install is not False:
        install(
            profile=args.install,
            shell_name=shell_name,
            shell_family=shell_family,
            reinstall=False,
        )
        return

    install(
        profile=args.reinstall,
        shell_name=shell_name,
        shell_family=shell_family,
        reinstall=True,
    )


def install(
    profile: str | None,
    shell_name: str,
    shell_family: str,
    reinstall: bool,
) -> None:
    if profile is None and shell_family != "cmd":
        raise ValueError("A profile must be specified with --install or --reinstall.")

    profile_path = None if profile is None else Path(profile).expanduser().resolve()

    plan = build_installation_plan(
        profile_path=profile_path,
        shell_family=shell_family,
        reinstall=reinstall,
        win_reg_edit=profile is None,
    )

    print_installation_plan(
        plan=plan,
        shell_name=shell_name,
        shell_family=shell_family,
    )

    if not confirm_installation():
        print("Installation aborted.")
        return

    generate_hook_script(shell_family)

    execute_installation_plan(
        plan=plan,
        shell_family=shell_family,
    )


def build_installation_plan(
    profile_path: Path | None,
    shell_family: str,
    reinstall: bool,
    win_reg_edit: bool,
) -> InstallationPlan:
    if win_reg_edit:
        if shell_family != "cmd" or profile_path is not None:
            raise ValueError("Invalid Windows registry installation state.")

        block = find_hook_launcher_win_reg()

        if block is None:
            action = "insert_reg"
        elif reinstall:
            action = "replace_reg"
        else:
            action = "skip"

        return InstallationPlan(
            profile_path=None,
            action=action,
            win_reg_edit=True,
            backup=action in {"insert_reg", "replace_reg"},
        )

    if profile_path is None:
        raise ValueError("A profile must be specified with --install or --reinstall.")

    if not profile_path.exists():
        raise FileNotFoundError(f'The profile "{profile_path}" does not exist.')

    if profile_path.is_dir():
        launcher_path = profile_path / get_hook_launcher_script_name(shell_family)

        if reinstall:
            action = "overwrite"
        elif launcher_path.exists():
            action = "skip"
        else:
            action = "create"

        return InstallationPlan(
            profile_path=launcher_path,
            action=action,
            win_reg_edit=False,
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
            win_reg_edit=False,
            backup=action in {"insert", "replace"},
        )

    raise ValueError(f'The profile "{profile_path}" is neither a file nor a directory.')


def print_installation_plan(
    plan: InstallationPlan,
    shell_name: str,
    shell_family: str,
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

    if plan.action == "insert_reg":
        print("Edit Windows registry:")
        print("  Insert the hook launcher call in the CMD AutoRun value.")
        return

    if plan.action == "replace_reg":
        print("Edit Windows registry:")
        print("  Remove the existing hook launcher block.")
        print("  Insert the hook launcher call in the CMD AutoRun value.")
        return

    if plan.action == "skip":
        if plan.win_reg_edit:
            print("No changes required:")
            print("  = Windows registry CMD AutoRun")
        else:
            print("No changes required:")
            print(f"  = {plan.profile_path}")
        return

    raise RuntimeError(f"Unknown installation action: {plan.action}")


def print_installation_backup(plan: InstallationPlan):
    if not plan.backup:
        return

    print()
    print("Backup:")

    if plan.win_reg_edit:
        print("  A backup of the Windows registry CMD AutoRun value")
        print("  will be created before editing.")
    else:
        print(f"  A backup of {plan.profile_path} will be created before editing.")


def confirm_installation() -> bool:
    answer = input("Continue with the installation? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def execute_installation_plan(
    plan: InstallationPlan,
    shell_family: str,
):
    if plan.action == "skip":
        return

    if plan.win_reg_edit:
        execute_windows_registry_installation(plan=plan)
        return

    if plan.profile_path is None:
        raise RuntimeError(
            "An installation plan without a profile path cannot be "
            "executed as a file installation."
        )

    profile_path = plan.profile_path

    if plan.backup:
        backup_file(path=profile_path)

    if plan.action in {"create", "overwrite"}:
        generate_hook_launcher_script(
            folder_path=profile_path.parent,
            shell_family=shell_family,
        )
        return

    if plan.action == "insert":
        insert_hook_launcher_code_block(
            script_path=profile_path,
            shell_family=shell_family,
        )
        return

    if plan.action == "replace":
        block = find_hook_launcher_code_block(
            script_path=profile_path,
            shell_family=shell_family,
        )

        if block is None:
            raise RuntimeError(
                f'The hook launcher block in "{profile_path}" '
                "was removed before installation."
            )

        remove_hook_launcher_code_block(
            script_path=profile_path,
            block_positions=block,
        )

        insert_hook_launcher_code_block(
            script_path=profile_path,
            shell_family=shell_family,
        )
        return

    raise RuntimeError(f"Unknown installation action: {plan.action}")


def execute_windows_registry_installation(
    plan: InstallationPlan,
):
    if plan.backup:
        backup_autorun_win_reg()

    if plan.action == "insert_reg":
        add_hook_launcher_to_autorun_reg()
        return

    if plan.action == "replace_reg":
        block = find_hook_launcher_win_reg()

        if block is None:
            raise RuntimeError(
                "The hook launcher block in the Windows registry "
                "AutoRun value was removed before installation."
            )

        remove_hook_launcher_from_autorun_reg(
            block_positions=block,
        )

        add_hook_launcher_to_autorun_reg()
        return

    raise RuntimeError(f"Unknown registry installation action: {plan.action}")
