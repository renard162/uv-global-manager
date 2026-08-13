import argparse
import os
import sys

from .commands import activate as activate_command
from .commands import create as create_command
from .commands import delete as delete_command
from .commands import list as list_command
from .commands import makeproject as makeproject_command
from .commands import setup as setup_command
from .common.utils import which_path_only as which

COMMANDS = {
    "activate": activate_command,
    "list": list_command,
    "create": create_command,
    "delete": delete_command,
    "makeproject": makeproject_command,
    "setup": setup_command,
}


def main():
    try:
        integrity_check()
        parser = argparse.ArgumentParser(
            prog="uve",
            description=(
                "Manage global Python virtual environments using UV, including "
                "environments created from Python installations managed by "
                '"uv python", and create UV projects from existing global virtual '
                "environments as project templates."
            ),
        )

        sub = parser.add_subparsers(dest="command")

        for command in COMMANDS.values():
            command.register(sub)

        help_parser = sub.add_parser(
            "help",
            help="Display help for a command.",
            description="Display help for uve or for a specific command.",
            allow_abbrev=False,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""\
Examples:
    uve help
    uve help activate
    uve help list
    uve help create
    uve help delete
    uve help make-project
    uve help setup
    uve help help
""",
        )

        help_parser.add_argument(
            "help_command",
            nargs="?",
            choices=tuple(sub.choices),
            metavar="COMMAND",
            help="Command for which to display help.",
        )

        help_parser.set_defaults(
            func=help_run,
            parser=parser,
            subparsers=sub,
        )

        args = parser.parse_args()

        if args.command is None:
            parser.print_help()
            return 0

        if args.command == "help":
            return args.func(args)

        return args.func(args)

    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        raise SystemExit(130)

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


def help_run(args):
    if args.help_command is None:
        args.parser.print_help()
        return 0

    args.subparsers.choices[args.help_command].print_help()
    return 0


def get_commands_list() -> list[str]:
    return list(COMMANDS.keys())


def integrity_check():
    if os.name not in ("nt", "posix"):
        raise OSError(f"Unsupported operating system: {os.name}")

    if (which("uv") is None) or (which("uvx") is None):
        raise FileNotFoundError(
            "Required executables 'UV' and 'UVX' was not found in the PATH. "
            "Install UV and ensure it is accessible from the command line before using uv-global-wrapper."
        )
