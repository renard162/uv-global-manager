from __future__ import annotations

import os
from pathlib import Path

from shellingham import ShellDetectionFailure, detect_shell

BASE_PYTHON_VERSION = "3.13"

ANY_OS_SHELLS = {
    "bash": "posix",
    "ksh": "posix",
    "zsh": "posix",
    "csh": "cshell",
    "tcsh": "cshell",
    "fish": "fish",
    "powershell": "powershell",
    "pwsh": "powershell",
    "nu": "nushell",
}

POSIX_ONLY_SHELLS = {}

WINDOWS_ONLY_SHELLS = {
    "cmd": "cmd",
    "xonsh": "xonsh",
}


def venvs_root_path(abs_path=True) -> Path:
    root_folder = Path("uvEnvs")
    if abs_path:
        return Path.home() / root_folder
    return root_folder


def resources_path(abs_path=True) -> Path:
    return venvs_root_path(abs_path) / ".resources"


def hook_script_path(abs_path=True) -> Path:
    return resources_path(abs_path) / "Hook_Scripts"


def repository_path(abs_path=True) -> Path:
    return resources_path(abs_path) / "Repository"


def venv_script_folder_name() -> str:
    folder_name_dict = {
        "posix": "bin",
        "nt": "Scripts",
    }
    return folder_name_dict.get(os.name, "")


def venv_script_path(venv_name: str, abs_path=True) -> Path:
    return venvs_root_path(abs_path) / venv_name / venv_script_folder_name()


def path_as_posix(base_path: Path) -> str:
    return base_path.as_posix()


def path_as_windows(base_path: Path) -> str:
    return base_path.as_posix().replace("/", "\\")


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
