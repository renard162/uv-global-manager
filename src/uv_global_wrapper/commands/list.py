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

    parser.add_argument(
        "-i",
        "--implementation",
        help="Filter environments by Python implementation.",
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

    if not any(
        (
            args.all,
            args.implementation,
            # args.python_version,
        )
    ):
        rows = [[environment.name] for environment in environments]
        headers = ["Environment"]
        print(format_table(headers, rows))
        return

    environment_data = load_environment_data(environments)

    if args.implementation:
        environment_data = filter_by_implementation(
            environment_data,
            args.implementation,
        )

    if args.all:
        rows = [
            [
                environment["name"],
                environment["version_info"],
                environment["implementation"],
            ]
            for environment in environment_data
        ]

        headers = [
            "Environment",
            "Python Version",
            "Implementation",
        ]

    else:
        rows = [[environment["name"]] for environment in environment_data]
        headers = ["Environment"]

    print(format_table(headers, rows))


def parse_pyvenv_cfg(path: Path) -> dict[str, str]:
    config = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator:
            config[key.strip()] = value.strip()
    return config


def load_environment_data(environments: list[Path]) -> list[dict[str, str]]:
    data = []
    for environment in environments:
        config = parse_pyvenv_cfg(environment / "pyvenv.cfg")
        data.append(
            {
                "name": environment.name,
                "version_info": config.get("version_info", ""),
                "implementation": config.get("implementation", ""),
            }
        )
    return data


def filter_by_implementation(
    environments: list[dict[str, str]], implementation: str
) -> list[dict[str, str]]:
    implementation = implementation.strip().lower()

    return [
        environment
        for environment in environments
        if environment["implementation"].strip().lower() == implementation
    ]


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
