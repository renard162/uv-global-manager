import os
from pathlib import Path

from shellingham import detect_shell, ShellDetectionFailure

BASE_PYTHON_VERSION = "3.13"


def venvs_root_path() -> Path:
    return Path.home() / ".uvEnvs"


def resources_path() -> Path:
    return venvs_root_path() / ".resources"


def repository_path() -> Path:
    return resources_path() / "Repository"


def venv_script_path(venv_name: str) -> Path:
    os_name = os.name
    if os_name == "posix":
        return venvs_root_path() / venv_name / "bin"

    if os_name == "nt":
        return venvs_root_path() / venv_name / "Scripts"


def get_parent_shell() -> str:
    os_name = os.name
    shell_name, _ = detect_shell()

    supported_shells = [
        "sh",
        "bash",
        "dash",
        "ash",
        "csh",
        "tcsh",
        "ksh",
        "zsh",
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
