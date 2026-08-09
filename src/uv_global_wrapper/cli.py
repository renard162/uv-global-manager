import argparse
import os
import sys

from .commands import (
    activate,
    create,
    delete,
    list,
    makeproject,
    setup,
)
from .utils import print_warning
from .utils import which_path_only as which


def main():
    # try:
    parser = argparse.ArgumentParser(prog="avg")
    sub = parser.add_subparsers(dest="command")

    activate.register(sub)
    list.register(sub)
    create.register(sub)
    delete.register(sub)
    makeproject.register(sub)
    setup.register(sub)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()

    integrity_check()

    if args.command is None:
        return 0

    return args.func(args)

    # except KeyboardInterrupt:
    #     print("\nOperation cancelled.", file=sys.stderr)
    #     raise SystemExit(130)

    # except Exception as exc:  # noqa: BLE001
    #     print(f"Error: {exc}", file=sys.stderr)
    #     raise SystemExit(1)


def integrity_check():
    if os.name not in ("nt", "posix"):
        raise OSError(f"Unsupported operating system: {os.name}")

    if (which("uv") is None) or (which("uvx") is None):
        raise FileNotFoundError(
            "Required executables 'UV' and 'UVX' was not found in the PATH. "
            "Install UV and ensure it is accessible from the command line before using uv-global-wrapper."
        )

    if which("uvg") is None:
        print_warning("UVG is not available in PATH.", pre_message="\n")
