from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from shellingham import ShellDetectionFailure, detect_shell

ANY_OS_SHELLS = {
    "bash": "posix",
    "pwsh": "powershell",
    "nu": "nushell",
    "xonsh": "xonsh",
}

POSIX_ONLY_SHELLS = {
    "ksh": "posix",
    "zsh": "posix",
    "csh": "cshell",
    "tcsh": "cshell",
    "fish": "fish",
}

WINDOWS_ONLY_SHELLS = {
    "powershell": "powershell",
    "cmd": "cmd",
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
