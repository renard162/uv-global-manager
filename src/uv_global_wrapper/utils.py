from __future__ import annotations

import os
from pathlib import Path

from shellingham import ShellDetectionFailure, detect_shell

BASE_PYTHON_VERSION = "3.13"


def venvs_root_path() -> Path:
    return Path.home() / ".uvEnvs"


def resources_path() -> Path:
    return venvs_root_path() / ".resources"


def repository_path() -> Path:
    return resources_path() / "Repository"


def venv_script_path(venv_name: str) -> Path | None:
    os_name = os.name
    if os_name == "posix":
        return venvs_root_path() / venv_name / "bin"

    if os_name == "nt":
        return venvs_root_path() / venv_name / "Scripts"


def get_parent_shell() -> str:
    os_name = os.name
    shell_name, _ = detect_shell()

    supported_shells = [
        "bash",
        "ksh",
        "zsh",
        "csh",
        "tcsh",
        "fish",
        "powershell",
        "pwsh",
        "nu",
    ]
    if os_name == "nt":
        supported_shells.extend(["cmd", "xonsh"])
    elif os_name == "posix":
        supported_shells.extend([])

    if shell_name not in supported_shells:
        raise ShellDetectionFailure(f"Unsupported command shell: {shell_name}")

    return shell_name


def get_script_extension(shell_name: str) -> str:
    extension_dict = {
        "bash": "",
        "ksh": "",
        "zsh": "",
        "csh": ".csh",
        "tcsh": ".csh",
        "fish": ".fish",
        "cmd": ".bat",
        "powershell": ".ps1",
        "pwsh": ".ps1",
        "xonsh": ".xsh",
        "nu": ".nu",
    }
    extension = extension_dict.get(shell_name, None)

    if extension is None:
        raise ShellDetectionFailure(f"Unsupported command shell: {shell_name}")

    return extension
