from pathlib import Path

from ..paths import hook_script_path
from .renders import (
    render_shell_hook_call,
    render_shell_hook_call_insertion,
    render_shell_hook_script,
)

HOOK_SCRIPTS = {
    "posix": "uve-posix.sh",
    "cshell": "uve-cshell.csh",
    "fish": "uve-fish.fish",
    "powershell": "uve-powershell.ps1",
    "cmd": "uve-cmd.bat",
    "nushell": "uve-nushell.nu",
    "xonsh": "uve-xonsh.xsh",
}


def generate_hook_script(shell_family: str) -> None:
    script_path = hook_script_path() / HOOK_SCRIPTS.get(shell_family, "")


def generate_script(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    print("Breakpoint Here")
