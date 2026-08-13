from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..common.hooks.generator_reg import (
    AUTORUN_KEY,
    AUTORUN_VALUE,
    add_hook_launcher_to_autorun_reg,
    backup_autorun_win_reg,
    find_hook_launcher_win_reg,
    remove_hook_launcher_from_autorun_reg,
)
from ..common.hooks.generator_script import (
    SCRIPT_EXTENSIONS,
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
    backup_folder_path,
    hook_script_path,
    repository_path,
    venvs_root_path,
)
from ..common.repository import (
    EXTERNAL_PACKAGES,
    download_package,
)
from ..common.utils import (
    create_path_tree,
    get_parent_shell,
)

WIN_REGISTRY_PROFILE = "win-registry"


def register(subparsers):
    parser = subparsers.add_parser(
        "setup",
        help="Install shell hooks or manage the local package repository.",
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Install shell hooks, generate hook scripts, or manage "
            "the local package repository."
        ),
        epilog=f"""\
Supported Shells:
    posix       : bash, ksh, zsh
    cshell      : csh, tcsh
    fish        : fish
    nushell     : nu
    xonsh       : xonsh
    powershell  : pwsh, powershell
    cmd         : cmd
    clink-cmd   : cmd with clink addon

Compatibility:
    cmd and csh have limited compatibility: only the shell hook is available,
    without autocomplete support. For cmd, install Clink and use the
    clink-cmd addon to provide full shell functionality, including
    autocomplete. For csh, use tcsh instead, which provides the same
    additional shell functionality, including autocomplete.

    Installing the cmd hook through {WIN_REGISTRY_PROFILE} modifies the
    Windows CMD AutoRun registry configuration. This can cause bugs or
    crashes in terminal programs that provide their own autorun mechanism,
    such as ConEmu, Cmder, and even Clink. Prefer using the Clink addon for
    cmd and installing the hook through the clink-cmd shell option instead,
    as it provides additional functionality such as autocomplete and performs
    autorun through a script, isolating the modification from other terminal programs.

Examples:
    uve setup --install ~/.bashrc
    uve setup --reinstall ~/.config/fish/config.fish
    uve setup --hook-script nushell
    uve setup --install C:\\Cmder\\config\\ --shell clink-cmd
    uve setup --install {WIN_REGISTRY_PROFILE} --shell cmd
    uve setup --update-repo
    uve setup --clear-repo
""",
    )

    install_group = parser.add_mutually_exclusive_group()

    install_group.add_argument(
        "--install",
        metavar="PROFILE",
        help=(
            "Install shell hooks into PROFILE. "
            f"Use '{WIN_REGISTRY_PROFILE}' as PROFILE to install the hook "
            "in the Windows CMD AutoRun configuration."
        ),
    )

    install_group.add_argument(
        "--reinstall",
        metavar="PROFILE",
        help=(
            "Reinstall/Update/Recover shell hooks into PROFILE. "
            f"Use '{WIN_REGISTRY_PROFILE}' as PROFILE to install the hook "
            "in the Windows CMD AutoRun configuration."
        ),
    )

    install_group.add_argument(
        "--hook-script",
        choices=SCRIPT_EXTENSIONS.keys(),
        help="Generate only the hook script for the specified shell.",
    )

    install_group.add_argument(
        "--update-repo",
        action="store_true",
        help="Update the local package repository to the latest package versions.",
    )

    install_group.add_argument(
        "--clear-repo",
        action="store_true",
        help="Delete all files from the local package repository.",
    )

    parser.add_argument(
        "-s",
        "--shell",
        choices=SCRIPT_EXTENSIONS.keys(),
        help=(
            "Select the shell explicitly instead of detecting it automatically "
            "when installing or reinstalling shell hooks. "
            "The clink-cmd addon is not auto-detected because it extends cmd "
            "through Clink and must always be selected explicitly with this option."
        ),
    )

    parser.set_defaults(func=setup_run, parser=parser)


def setup_run(args: argparse.Namespace):
    if (
        (args.install is None)
        and (args.reinstall is None)
        and (args.hook_script is None)
        and (not args.update_repo)
        and (not args.clear_repo)
    ):
        args.parser.print_help()
        return

    if args.update_repo:
        fail_safe_repository_update()
        return

    if args.clear_repo:
        clear_repository()
        return

    if args.hook_script is not None:
        shell_name, shell_family = None, args.hook_script
    elif args.shell is not None:
        shell_name, shell_family = None, args.shell
    else:
        shell_name, shell_family = get_parent_shell()

    if args.hook_script is not None:
        install_hook_script_only(shell_family=shell_family)
        return

    if args.install is not None:
        install(
            profile=args.install,
            shell_name=shell_name,
            shell_family=shell_family,
            reinstall=False,
        )
        return

    install(
        profile=str(args.reinstall),
        shell_name=shell_name,
        shell_family=shell_family,
        reinstall=True,
    )


def install(
    profile: str,
    shell_name: str | None,
    shell_family: str,
    reinstall: bool,
) -> None:
    win_reg_edit = profile == WIN_REGISTRY_PROFILE
    profile_path = None if win_reg_edit else Path(profile).expanduser().resolve()

    plan = build_installation_plan(
        profile_path=profile_path,
        shell_family=shell_family,
        reinstall=reinstall,
        win_reg_edit=win_reg_edit,
    )

    print_installation_plan(
        plan=plan,
        shell_name=shell_name,
        shell_family=shell_family,
    )

    if not confirm_operation():
        print("\nInstallation aborted.")
        return

    create_folder_tree()
    generate_hook_script(shell_family)
    execute_installation_plan(
        plan=plan,
        shell_family=shell_family,
    )

    print("\nInstallation completed successfully.")
    print("Reopen the shell for the changes to take effect.")


def build_installation_plan(
    profile_path: Path | None,
    shell_family: str,
    reinstall: bool,
    win_reg_edit: bool,
) -> InstallationPlan:
    if win_reg_edit:
        if (shell_family != "cmd") or (profile_path is not None) or (os.name != "nt"):
            raise ValueError(
                "Windows registry installation is only supported on Windows."
            )

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
    shell_name: str | None,
    shell_family: str,
):
    shell_message = (
        f"Shell: {shell_family}"
        if (shell_name is None)
        else f"Shell: {shell_name} ({shell_family})"
    )
    print("\nThe following changes will be made:\n")
    print(shell_message)
    print()

    limited_shell = shell_name in {"cmd", "csh"} or (
        shell_name is None and shell_family in {"cmd", "cshell"}
    )

    if limited_shell:
        limited_shell_name = (
            shell_name
            if shell_name is not None
            else ("csh" if shell_family == "cshell" else "cmd")
        )
        print(
            f"WARNING: integration with {limited_shell_name} is limited "
            "to the shell hook and does not provide autocomplete."
        )
        print()

    print_installation_action(
        plan=plan,
        shell_family=shell_family,
    )
    print_installation_backup(plan)

    print()


def print_installation_action(
    plan: InstallationPlan,
    shell_family: str,
):
    if plan.action == "create":
        print("Create file:")
        print()
        print(f"  + {plan.profile_path}")
        print()
        print("  The hook autorun script will be created.")
        return

    if plan.action == "overwrite":
        print("Overwrite file:")
        print()
        print(f"  ~ {plan.profile_path}")
        print()
        print("  The hook autorun script will be regenerated.")
        return

    if plan.action == "insert":
        if plan.profile_path is None:
            raise RuntimeError(
                "An installation plan for a script must have a profile path."
            )

        print("Edit file:")
        print()
        print(f"  ~ {plan.profile_path}")
        print()
        print("  The following command will be inserted at the end of")
        print(f"  {plan.profile_path.name}:")
        print()
        print(f"    {render_shell_hook_call(shell_family)}")
        return

    if plan.action == "replace":
        if plan.profile_path is None:
            raise RuntimeError(
                "An installation plan for a script must have a profile path."
            )

        print("Edit file:")
        print()
        print(f"  ~ {plan.profile_path}")
        print()
        print("  The existing hook launcher block will be removed.")
        print()
        print("  The following command will then be inserted at the end of")
        print(f"  {plan.profile_path.name}:")
        print()
        print(f"    {render_shell_hook_call(shell_family)}")
        return

    if plan.action == "insert_reg":
        print("Edit Windows registry:")
        print()
        print("  Registry key:")
        print()
        print(f"    {AUTORUN_KEY!r}")
        print()
        print(f"  Registry value: {AUTORUN_VALUE!r}")
        print()
        print("  The following command will be added to the Windows AutoRun")
        print("  configuration:")
        print()
        print(f"    {render_shell_hook_call(shell_family)}")
        print()
        print(
            "  WARNING: modifying the Windows CMD AutoRun configuration can cause bugs"
        )
        print("  in alternative shells and terminal programs such as Cmder.")
        print("  The registry backup can be used to revert this change.")
        return

    if plan.action == "replace_reg":
        print("Edit Windows registry:")
        print()
        print("  Registry key:")
        print()
        print(f"    {AUTORUN_KEY!r}")
        print()
        print("  Registry value:")
        print()
        print(f"    {AUTORUN_VALUE!r}")
        print()
        print("  The existing hook launcher block will be removed.")
        print()
        print("  The following command will then be added to the Windows")
        print("  AutoRun configuration:")
        print()
        print(f"    {render_shell_hook_call(shell_family)}")
        print()
        print(
            "  WARNING: modifying the Windows CMD AutoRun configuration can cause bugs"
        )
        print("  in alternative shells and terminal programs such as Cmder.")
        print("  The registry backup can be used to revert this change.")
        return

    if plan.action == "skip":
        if plan.win_reg_edit:
            print("No changes required:")
            print()
            print("  Windows registry CMD AutoRun")
        else:
            print("No changes required:")
            print()
            print(f"  {plan.profile_path}")
        return

    raise RuntimeError(f"Unknown installation action: {plan.action}")


def print_installation_backup(plan: InstallationPlan):
    if not plan.backup:
        return

    print("\nBackup:")

    if plan.win_reg_edit:
        print("  A backup of the Windows registry CMD AutoRun value")
        print("  will be created before editing.")
        print("  This backup can be used to revert the registry change.")
    else:
        print(f"  A backup of {plan.profile_path} will be created before editing.")


def confirm_operation() -> bool:
    answer = input("Continue? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def execute_installation_plan(plan: InstallationPlan, shell_family: str):
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
        backup_message, backup_error = backup_file(path=profile_path)

        if backup_message is not None:
            if backup_error:
                print("Error generating backup file:\n")
                print(backup_message)
            else:
                print("Generated backup file:\n")
                print(backup_message)

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

        if block is not None:
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


def execute_windows_registry_installation(plan: InstallationPlan):
    if os.name != "nt":
        raise RuntimeError(
            "Windows registry installation is only supported on Windows."
        )

    if plan.backup:
        backup_message, backup_error = backup_autorun_win_reg()

        if backup_error:
            print("Error generating Windows registry backup:\n")
            print(backup_message)
        else:
            print("Generated Windows registry backup:\n")
            print(backup_message)

    if plan.action == "insert_reg":
        add_hook_launcher_to_autorun_reg()
        return

    if plan.action == "replace_reg":
        block = find_hook_launcher_win_reg()

        if block is not None:
            remove_hook_launcher_from_autorun_reg(block)

        add_hook_launcher_to_autorun_reg()
        return

    raise RuntimeError(f"Unknown registry installation action: {plan.action}")


def create_folder_tree() -> None:
    folder_tree = [
        hook_script_path(),
        repository_path(),
        backup_folder_path(),
        venvs_root_path(),
    ]

    for folder in folder_tree:
        create_path_tree(folder)


def install_hook_script_only(shell_family: str) -> None:
    create_folder_tree()
    generate_hook_script(shell_family)

    print("\n\nThe hook script was generated successfully.")
    print("Run the following command or add it to your shell profile:")
    print(f"\n{render_shell_hook_call(shell_family)}\n")
    input("Press Enter to exit.")


def fail_safe_repository_update() -> None:
    original_repository_folder = repository_path()
    backup_repository_folder = (
        original_repository_folder.parent / f"{original_repository_folder.name}_bck"
    )

    print(
        "WARNING: all packages in the local package repository "
        "will be updated to their latest available versions.\n"
    )
    print(f"Repository: {original_repository_folder}\n")

    if not confirm_operation():
        print("\nRepository update aborted.")
        return

    if not original_repository_folder.is_dir():
        create_path_tree(original_repository_folder)

    if backup_repository_folder.exists():
        shutil.rmtree(backup_repository_folder)

    original_repository_folder.rename(backup_repository_folder)
    create_path_tree(original_repository_folder)

    try:
        for package in EXTERNAL_PACKAGES.values():
            result = download_package(
                package=package,
                raise_on_fail=False,
                print_stdout=True,
                print_stderr=True,
            )

            if result != 0:
                print("\nFailed to update local package repository.")
                print("Removing incomplete repository.")
                shutil.rmtree(original_repository_folder)

                print("Restoring previous repository.")
                backup_repository_folder.rename(original_repository_folder)
                return

        print("\nLocal package repository updated successfully.")
        print(f"Removing backup: {backup_repository_folder}")
        shutil.rmtree(backup_repository_folder)
        return

    except Exception:
        if original_repository_folder.exists():
            shutil.rmtree(original_repository_folder)

        if backup_repository_folder.exists():
            backup_repository_folder.rename(original_repository_folder)

        raise


def clear_repository() -> None:
    repository = repository_path()

    print(
        "WARNING: all files and directories in the local package "
        "repository will be deleted.\n"
    )
    print(f"Repository: {repository}\n")

    if not confirm_operation():
        print("\nRepository cleanup aborted.")
        return

    if repository.exists():
        shutil.rmtree(repository)

    create_path_tree(repository)

    print("\nLocal package repository cleared successfully.")


@dataclass
class InstallationPlan:
    profile_path: Path | None
    action: str
    win_reg_edit: bool
    backup: bool = False
