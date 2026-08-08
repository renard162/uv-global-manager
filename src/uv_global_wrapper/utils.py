import os
from pathlib import Path

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

    raise OSError(f"Unsupported operating system: {os_name}")
