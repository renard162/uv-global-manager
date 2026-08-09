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


def venvs_root_path(abs_path=True) -> Path:
    root_folder = Path(".uvEnvs")
    if abs_path:
        return Path.home() / root_folder
    return root_folder


def resources_path(abs_path=True) -> Path:
    return venvs_root_path(abs_path) / ".resources"


def hook_script_path(abs_path=True) -> Path:
    return venvs_root_path(abs_path) / "Hook_Scripts"


def repository_path(abs_path=True) -> Path:
    return resources_path(abs_path) / "Repository"


def venv_script_path(venv_name: str, abs_path=True) -> Path:
    os_name = os.name
    if os_name == "posix":
        return venvs_root_path(abs_path) / venv_name / "bin"

    if os_name == "nt":
        return venvs_root_path(abs_path) / venv_name / "Scripts"

    return Path("")


def path_as_posix(base_path: Path) -> str:
    return base_path.as_posix()


def path_as_windows(base_path: Path) -> str:
    return base_path.as_posix().replace("/", "\\")


def path_as_windows_bash(base_path: Path) -> str:
    path_str = base_path.as_posix().replace(":", "").lower()
    return f"/{path_str}"


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


def get_script_extension(shell_family: str) -> str:
    extension_dict = {
        "posix": "",
        "c_shell": ".csh",
        "fish": ".fish",
        "powershell": ".ps1",
        "cmd": ".bat",
        "nushell": ".nu",
        "xonsh": ".xsh",
    }
    extension = extension_dict.get(shell_family, None)

    if extension is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return extension
