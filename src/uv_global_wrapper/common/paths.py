from __future__ import annotations

import os
from pathlib import Path


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
    return folder_name_dict.get(os.name, "__error")


def venv_script_path(venv_name: str, abs_path=True) -> Path:
    return venvs_root_path(abs_path) / venv_name / venv_script_folder_name()


def venv_interpreter_path(venv_name: str, abs_path=True) -> Path:
    venv_scripts = venv_script_path(venv_name, abs_path)
    interpreter_dict = {
        "posix": venv_scripts / "python",
        "nt": venv_scripts / "python.exe",
    }
    return interpreter_dict.get(os.name, Path("__error"))


def active_venv_path() -> Path | None:
    venv = os.environ.get("VIRTUAL_ENV")
    if venv is None:
        return None
    return Path(venv)


def path_as_posix(base_path: Path) -> str:
    return base_path.as_posix()


def path_as_windows(base_path: Path) -> str:
    return base_path.as_posix().replace("/", "\\")
