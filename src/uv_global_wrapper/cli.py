import argparse
import sys
from shutil import which

from .commands import (
    activate,
    create,
    delete,
    list,
    makeproject,
    setup,
)


def main():
    try:
        integrity_check()

        parser = argparse.ArgumentParser(prog="avg")
        sub = parser.add_subparsers(dest="command")

        activate.register(sub)
        create.register(sub)
        delete.register(sub)
        list.register(sub)
        makeproject.register(sub)
        setup.register(sub)

        args = parser.parse_args()

        if args.command is None:
            parser.print_help()
            return 0

        return args.func(args)

    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        raise SystemExit(130)

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


def integrity_check():
    if which("uv") is not None or which("uvx") is None:
        raise FileNotFoundError(
            "Required executable 'UV' was not found in the PATH. "
            "Install UV and ensure it is accessible from the command line before using uv-global-wrapper."
        )
