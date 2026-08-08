import argparse
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

    args.func(args)


def integrity_check():
    if (which("uv") is None) or (which("uvx") is None):
        raise FileNotFoundError(
            "Required executable 'UV' was not found in the PATH. Install UV and ensure it is accessible from the command line before using uv-global-wrapper."
        )
    return 0
