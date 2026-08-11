from __future__ import annotations

import argparse
import re
from pathlib import Path

from ..common.paths import venvs_root_path
from ..common.utils import (
    parse_pyvenv_cfg,
    print_table,
)


def register(subparsers):

    parser = subparsers.add_parser(
        "list",
        help="List global virtual environments.",
        description="Lists global virtual environments.",
        allow_abbrev=False,
    )

    parser.add_argument(
        "-i",
        "--implementation",
        help="Filter environments by Python implementation.",
    )

    parser.add_argument(
        "-p",
        "--python-version",
        help=(
            "Filter environments by Python version using PEP 440 specifiers. "
            "(e.g. ~=, >=, <=, ==, !=, >, <). Quote the value when it contains shell operators, "
            'e.g. ">=3.9".'
        ),
    )

    parser.add_argument(
        "-d",
        "--details",
        action="store_true",
        help="Show additional information about each virtual environment.",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics grouped by Python implementation and version.",
    )

    parser.set_defaults(
        func=list_run,
        parser=parser,
    )


def list_run(args: argparse.Namespace):
    if args.stats and any(
        (
            args.details,
            args.implementation,
            args.python_version,
        )
    ):
        args.parser.error("--stats cannot be combined with other options.")

    environments = sorted(
        path
        for path in venvs_root_path().iterdir()
        if path.is_dir() and (path / "pyvenv.cfg").is_file()
    )

    if args.stats:
        environment_data = load_environment_data(environments)

        rows = generate_stats(environment_data)

        headers = [
            "Implementation",
            "Python Version",
            "Environments",
        ]

        print(print_table(headers, rows))
        return

    if not any(
        (
            args.details,
            args.implementation,
            args.python_version,
        )
    ):
        rows = [[environment.name] for environment in environments]
        headers = ["Environment"]
        print(print_table(headers, rows))
        return

    environment_data = load_environment_data(
        environments,
        include_size=args.details,
    )

    if args.implementation:
        environment_data = filter_by_implementation(
            environment_data,
            args.implementation,
        )

    if args.python_version:
        environment_data = filter_by_python_version(
            environment_data,
            args.python_version,
        )

    if args.details:
        rows = [
            [
                environment["name"],
                environment["version_info"],
                environment["implementation"],
                environment["size_mb"],
            ]
            for environment in environment_data
        ]

        headers = [
            "Environment",
            "Python Version",
            "Implementation",
            "Size (MB)",
        ]

    else:
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

    print(print_table(headers, rows))


def load_environment_data(
    environments: list[Path],
    include_size: bool = False,
) -> list[dict[str, str]]:
    data = []

    for environment in environments:
        config = parse_pyvenv_cfg(environment / "pyvenv.cfg")

        environment_data = {
            "name": environment.name,
            "version_info": config.get("version_info", ""),
            "implementation": config.get("implementation", ""),
        }

        if include_size:
            environment_data["size_mb"] = (
                f"{get_directory_size(environment) / 1024**2:.2f}"
            )

        data.append(environment_data)

    return data


def get_directory_size(directory: Path) -> int:
    return sum(file.stat().st_size for file in directory.rglob("*") if file.is_file())


def filter_by_implementation(
    environments: list[dict[str, str]], implementation: str
) -> list[dict[str, str]]:
    implementation = implementation.strip().lower()

    return [
        environment
        for environment in environments
        if environment["implementation"].strip().lower() == implementation
    ]


def filter_by_python_version(
    environments: list[dict[str, str]],
    specification: str,
) -> list[dict[str, str]]:
    specification = specification.strip().lower()
    clauses = [clause.strip() for clause in specification.split(",") if clause.strip()]
    predicates = [parse_version_specifier(clause) for clause in clauses]
    return [
        environment
        for environment in environments
        if all(predicate(environment["version_info"]) for predicate in predicates)
    ]


def parse_version_specifier(specifier: str):
    match = re.fullmatch(
        r"(~=|>=|<=|!=|==|>|<)?\s*(\d+(?:\.\d+)*)",
        specifier.strip().lower(),
    )

    if not match:
        raise ValueError(f'Invalid Python version specifier: "{specifier}".')

    operator = match.group(1)
    version = tuple(int(part) for part in match.group(2).split("."))

    if operator is None:
        return lambda candidate: version_prefix_match(candidate, version)

    if operator == "~=":
        if len(version) < 2:
            raise ValueError(
                f'The compatible release operator "~=" requires '
                f'at least two version segments: "{specifier}".'
            )

        if len(version) == 2:
            upper_bound = (version[0] + 1,)
        else:
            upper_bound = version[:-2] + (version[-2] + 1,)

        return lambda candidate: (
            compare_versions(candidate, version) >= 0
            and compare_versions(candidate, upper_bound) < 0
        )

    compare_version_dict = {
        "==": lambda candidate: compare_versions(candidate, version) == 0,
        "!=": lambda candidate: compare_versions(candidate, version) != 0,
        ">=": lambda candidate: compare_versions(candidate, version) >= 0,
        "<=": lambda candidate: compare_versions(candidate, version) <= 0,
        ">": lambda candidate: compare_versions(candidate, version) > 0,
        "<": lambda candidate: compare_versions(candidate, version) < 0,
    }

    compare_version_func = compare_version_dict.get(operator, None)

    if compare_version_func is None:
        raise ValueError(f'Unsupported Python version specifier: "{specifier}".')

    return compare_version_func


def version_prefix_match(
    candidate: str,
    requested: tuple[int, ...],
) -> bool:
    candidate_version = parse_python_version(candidate)
    return candidate_version[: len(requested)] == requested


def compare_versions(
    left: str | tuple[int, ...],
    right: str | tuple[int, ...],
) -> int:
    left_version = parse_python_version(left) if isinstance(left, str) else left
    right_version = parse_python_version(right) if isinstance(right, str) else right
    length = max(len(left_version), len(right_version))
    left_version += (0,) * (length - len(left_version))
    right_version += (0,) * (length - len(right_version))
    return (left_version > right_version) - (left_version < right_version)


def parse_python_version(version: str) -> tuple[int, ...]:
    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)*)\s*",
        version,
    )

    if not match:
        raise ValueError(f'Invalid Python version: "{version}".')

    return tuple(int(part) for part in match.group(1).split("."))


def generate_stats(
    environments: list[dict[str, str]],
) -> list[list[str]]:
    stats = {}

    for environment in environments:
        key = (
            environment["implementation"],
            parse_python_version(environment["version_info"]),
        )

        stats[key] = stats.get(key, 0) + 1

    return [
        [
            implementation,
            ".".join(str(part) for part in version),
            str(count),
        ]
        for (implementation, version), count in sorted(stats.items())
    ]
