import argparse

from .commands import (
    activate,
    create,
    delete,
    list,
    makeproject,
    setup,
)


def main():
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
