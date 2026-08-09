from __future__ import annotations

import os
from pathlib import Path

from shellingham import ShellDetectionFailure, detect_shell

BASE_PYTHON_VERSION = "3.13"
ANY_OS_SHELLS = {
    "bash": "posix",
    "ksh": "posix",
    "zsh": "posix",
    "csh": "c_shell",
    "tcsh": "c_shell",
    "fish": "fish",
    "powershell": "powershell",
    "pwsh": "powershell",
    "nu": "nushell",
}

WINDOWS_ONLY_SHELLS = {
    "cmd": "cmd",
    "xonsh": "xonsh",
}

POSIX_ONLY_SHELLS = {}


def venvs_root_path(complete_path=True) -> Path:
    root_folder = Path(".uvEnvs")
    if complete_path:
        return Path.home() / root_folder
    return root_folder


def resources_path(complete_path=True) -> Path:
    return venvs_root_path(complete_path) / ".resources"


def repository_path(complete_path=True) -> Path:
    return resources_path(complete_path) / "Repository"


def venv_script_path(venv_name: str, complete_path=True) -> Path | None:
    os_name = os.name
    if os_name == "posix":
        return venvs_root_path(complete_path) / venv_name / "bin"

    if os_name == "nt":
        return venvs_root_path(complete_path) / venv_name / "Scripts"


def get_parent_shell() -> tuple[str, str]:
    os_name = os.name
    shell_name, _ = detect_shell()

    supported_shells = ANY_OS_SHELLS.copy()
    if os_name == "nt":
        supported_shells.update(WINDOWS_ONLY_SHELLS)
    elif os_name == "posix":
        supported_shells.update(POSIX_ONLY_SHELLS)

    if shell_name not in supported_shells:
        raise ShellDetectionFailure(f"Unsupported command shell: {shell_name}")

    shell_family = supported_shells[shell_name]
    return shell_name, shell_family


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
