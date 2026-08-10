from __future__ import annotations

import argparse
from pathlib import Path

from ..common.utils import venvs_root_path


def register(subparsers):

    parser = subparsers.add_parser(
        "list",
        help="List global virtual environments.",
        description="Lists global virtual environments.",
        allow_abbrev=False,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show additional information about each virtual environment.",
    )

    parser.set_defaults(
        func=list_run,
        parser=parser,
    )


def list_run(args: argparse.Namespace):
    environments = sorted(
        path
        for path in venvs_root_path().iterdir()
        if path.is_dir() and (path / "pyvenv.cfg").is_file()
    )

    if args.all:
        rows = []

        for environment in environments:
            config = parse_pyvenv_cfg(environment / "pyvenv.cfg")

            rows.append(
                [
                    environment.name,
                    config.get("version_info", ""),
                    config.get("implementation", ""),
                ]
            )

        headers = [
            "Environment",
            "Python Version",
            "Implementation",
        ]

    else:
        rows = [[environment.name] for environment in environments]
        headers = ["Environment"]

    print(format_table(headers, rows))


def parse_pyvenv_cfg(path: Path) -> dict[str, str]:
    config = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")

        if separator:
            config[key.strip()] = value.strip()

    return config


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    columns = [headers, *rows]
    widths = [max(len(row[index]) for row in columns) for index in range(len(headers))]

    def format_row(row: list[str]) -> str:
        return "  ".join(value.ljust(width) for value, width in zip(row, widths))

    separator = "  ".join("-" * width for width in widths)
    lines = [
        format_row(headers),
        separator,
        *(format_row(row) for row in rows),
    ]

    return "\n".join(lines)
