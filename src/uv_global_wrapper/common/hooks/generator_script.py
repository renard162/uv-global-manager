import shutil
from pathlib import Path

from shellingham import ShellDetectionFailure

from ..paths import backup_folder_path, hook_script_path
from ..utils import create_path_tree
from .renders import (
    HOOK_SCRIPT_NAMES,
    render_insert_block_marker_end,
    render_insert_block_marker_init,
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
    hook_script_folder = hook_script_path()
    create_path_tree(hook_script_folder)
    script_name = HOOK_SCRIPT_NAMES.get(shell_family, None)
    if script_name is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")
    script_path = hook_script_folder / script_name
    generate_script(
        script_path=script_path,
        content=render_shell_hook_script(shell_family),
    )


def generate_hook_launcher_script(folder_path: Path, shell_family: str) -> None:
    script_path = folder_path / get_hook_launcher_script_name(shell_family)
    generate_script(
        script_path=script_path,
        content=render_shell_hook_call(shell_family),
    )


def insert_hook_launcher_code_block(script_path: Path, shell_family: str) -> None:
    hook_call_string = render_shell_hook_call_insertion(shell_family)
    with script_path.open("ab") as file:
        file.write(hook_call_string.encode("ascii"))


def find_hook_launcher_code_block(
    script_path: Path, shell_family: str
) -> tuple[int, int] | None:
    start_marker = render_insert_block_marker_init(shell_family).encode("ascii")
    end_marker = render_insert_block_marker_end(shell_family).encode("ascii")
    script_content = script_path.read_bytes()

    start = script_content.find(start_marker)
    if start == -1:
        return None

    end = script_content.find(end_marker, start + len(start_marker))
    if end == -1:
        return None

    end += len(end_marker)
    return start, end


def remove_hook_launcher_code_block(
    script_path: Path, block_positions: tuple[int, int]
) -> None:
    start, end = block_positions
    content = script_path.read_bytes()
    script_path.write_bytes(content[:start] + content[end:])


def get_hook_launcher_script_name(shell_family: str):
    return f"{HOOK_LAUNCHER_SCRIPT_NAME}.{SCRIPT_EXTENSIONS[shell_family]}"


def generate_script(script_path: Path, content: str) -> None:
    script_path.write_text(content, encoding="utf-8")


def backup_file(path: Path) -> tuple[str | None, bool]:
    if not path.is_file():
        return None, False

    try:
        backup_folder = backup_folder_path()
        create_path_tree(backup_folder)
        backup_files = list(backup_folder.glob(f"{path.name}.bak*"))

        if not backup_files:
            backup_path = backup_folder / f"{path.name}.bak"
        else:
            backup_files.sort(key=lambda bck: bck.suffix)
            suffix = backup_files[-1].suffix.removeprefix(".bak")

            if suffix.isdigit():
                suffix = str(int(suffix) + 1)
            else:
                suffix += "0"

            backup_path = backup_folder / f"{path.name}.bak{suffix}"

        shutil.copy2(path, backup_path)

    except OSError as exc:
        return str(exc), True

    return backup_path.name, False


if __name__ == "__main__":
    print("Breakpoint Here")
