import shutil
from pathlib import Path

from ..paths import hook_script_path
from .renders import (
    COMMENT_MARKERS,
    HOOK_MARKER,
    HOOK_SCRIPT_NAMES,
    render_shell_hook_call,
    render_shell_hook_call_insertion,
    render_shell_hook_script,
)

HOOK_LAUNCHER_SCRIPT_NAME = "uve-hook-launch"

SCRIPT_EXTENSIONS = {
    "posix": "sh",
    "cshell": "csh",
    "fish": "fish",
    "powershell": "ps1",
    "cmd": "bat",
    "nushell": "nu",
    "xonsh": "xsh",
}


def generate_hook_script(shell_family: str) -> None:
    script_path = hook_script_path() / HOOK_SCRIPT_NAMES[shell_family]
    generate_script(
        script_path=script_path,
        content=render_shell_hook_script(shell_family),
    )


def generate_hook_launcher_script(folder_path: Path, shell_family: str) -> None:
    script_path = (
        folder_path / f"{HOOK_LAUNCHER_SCRIPT_NAME}.{SCRIPT_EXTENSIONS[shell_family]}"
    )
    generate_script(
        script_path=script_path,
        content=render_shell_hook_call(shell_family),
    )


def insert_hook_launcher_command(script_path: Path, shell_family: str) -> None:
    backup_file(script_path)
    hook_call_string = render_shell_hook_call_insertion(shell_family)
    with script_path.open("ab") as file:
        file.write(hook_call_string.encode("ascii"))


def find_hook_block(script_path: Path, shell_family: str) -> tuple[int, int] | None:
    comment = COMMENT_MARKERS[shell_family]
    start_marker = (f"{comment} {HOOK_MARKER}-init").encode("ascii")
    end_marker = (f"{comment} {HOOK_MARKER}-end").encode("ascii")
    content = script_path.read_bytes()

    start = content.find(start_marker)
    if start == -1:
        return None

    end = content.find(end_marker, start + len(start_marker))
    if end == -1:
        return None

    end += len(end_marker)
    return start, end


def generate_script(script_path: Path, content: str) -> None:
    script_path.write_text(content, encoding="utf-8")


def backup_file(path: Path) -> str | None:
    if not path.is_file():
        return

    backup_files = list(path.parent.glob(f"{path.name}.bak*"))

    if not backup_files:
        backup_path = path.with_name(f"{path.name}.bak")
    else:
        backup_files.sort(
            key=lambda backup: backup.suffix,
        )

        suffix = backup_files[-1].suffix.removeprefix(".bak")

        if suffix.isdigit():
            suffix = str(int(suffix) + 1)
        else:
            suffix += "0"

        backup_path = path.with_name(f"{path.name}.bak{suffix}")

    shutil.copy2(path, backup_path)
    return backup_path.name


if __name__ == "__main__":
    print("Breakpoint Here")
