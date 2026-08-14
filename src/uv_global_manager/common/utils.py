from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from shellingham import ShellDetectionFailure, detect_shell

# Shells are grouped by familly not by shell name,
# for this reason ksh and zsh is "any os" for example
ANY_OS_SHELLS = {
    "bash": "posix",
    "ksh": "posix",
    "zsh": "posix",
    "pwsh": "powershell",
    "powershell": "powershell",
    "nu": "nushell",
    "xonsh": "xonsh",
}

POSIX_ONLY_SHELLS = {
    "csh": "cshell",
    "tcsh": "cshell",
    "fish": "fish",
}

WINDOWS_ONLY_SHELLS = {
    "cmd": "cmd",
}


def get_parent_shell() -> tuple[str, str]:
    os_name = os.name
    shell_name, _ = detect_shell()

    supported_shells = ANY_OS_SHELLS.copy()
    if os_name == "posix":
        supported_shells.update(POSIX_ONLY_SHELLS)
    elif os_name == "nt":
        supported_shells.update(WINDOWS_ONLY_SHELLS)

    if shell_name not in supported_shells:
        raise ShellDetectionFailure(f"Unsupported command shell: {shell_name}")

    shell_family = supported_shells[shell_name]
    return shell_name, shell_family


def which_path_only(command: str) -> str | None:
    if os.name == "posix":
        return shutil.which(command)

    old_value = os.environ.get("NoDefaultCurrentDirectoryInExePath")

    try:
        os.environ["NoDefaultCurrentDirectoryInExePath"] = "1"
        return shutil.which(command)
    finally:
        if old_value is None:
            os.environ.pop("NoDefaultCurrentDirectoryInExePath", None)
        else:
            os.environ["NoDefaultCurrentDirectoryInExePath"] = old_value


def print_stderr(message: str):
    print(message, file=sys.stderr)


def print_table(headers: list[str], rows: list[list[str]]) -> str:
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


def parse_pyvenv_cfg(path: Path) -> dict[str, str]:
    config = {}

    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")

        if separator:
            config[key.strip()] = value.strip()

    return config


def create_path_tree(target_path: Path) -> None:
    home = Path.home()

    if not home.exists():
        raise FileNotFoundError(f'Home directory does not exist: "{home}"')

    target_path = target_path.absolute()
    relative_path = target_path.relative_to(home)

    current = home
    for part in relative_path.parts:
        current /= part
        current.mkdir(exist_ok=True)
