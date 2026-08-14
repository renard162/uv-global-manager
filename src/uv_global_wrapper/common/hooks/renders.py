from shellingham import ShellDetectionFailure

from ..paths import (
    hook_script_path,
    path_as_posix,
    path_as_windows,
)
from .templates import (
    template_clink_cmd_hook_script,
    template_cmd_hook_script,
    template_cshell_hook_script,
    template_fish_hook_script,
    template_nushell_hook_script,
    template_posix_hook_script,
    template_powershell_hook_script,
    template_xonsh_hook_script,
)

HOOK_SCRIPT_NAMES = {
    "posix": "uve-posix.sh",
    "cshell": "uve-cshell.csh",
    "fish": "uve-fish.fish",
    "powershell": "uve-powershell.ps1",
    "cmd": "uve-cmd.bat",
    "nushell": "uve-nushell.nu",
    "xonsh": "uve-xonsh.xsh",
    "clink-cmd": "uve-clink-cmd.lua",
}

HOOK_MARKER = "uv-global-manager-hook-call"

COMMENT_MARKERS = {
    "posix": "#",
    "cshell": "#",
    "fish": "#",
    "powershell": "#",
    "cmd": "REM",
    "nushell": "#",
    "xonsh": "#",
    "clink-cmd": "--",
}


def render_shell_hook_call_insertion(shell_family: str) -> str:
    return (
        "\n"
        f"{render_insert_block_marker_init(shell_family)}"
        f"{render_shell_hook_call(shell_family)}"
        f"{render_insert_block_marker_end(shell_family)}"
        "\n"
    )


def render_shell_hook_call(shell_family: str) -> str:
    hook_script_location = hook_script_path(abs_path=False)
    posix_location = path_as_posix(hook_script_location)
    windows_location = path_as_windows(hook_script_location)

    hook_script = HOOK_SCRIPT_NAMES.get(shell_family)
    hook_calls_dict = {
        "posix": f'source "$HOME/{posix_location}/{hook_script}"',
        "cshell": f'source "$HOME/{posix_location}/{hook_script}"',
        "fish": f'source "$HOME/{posix_location}/{hook_script}"',
        "powershell": f'. "$HOME\\{windows_location}\\{hook_script}"',
        "cmd": f'doskey uve=call "%USERPROFILE%\\{windows_location}\\{hook_script}" $*',
        "nushell": f'source ($nu.home-dir | path join "{posix_location}/{hook_script}")',
        "xonsh": f'source "~/{posix_location}/{hook_script}"',
        "clink-cmd": f'dofile(clink.get_env("USERPROFILE") .. "/{posix_location}/{hook_script}")',
    }

    hook_call = hook_calls_dict.get(shell_family, None)

    if hook_call is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return hook_call


def render_shell_hook_script(shell_family: str) -> str:
    hook_scripts_dict = {
        "posix": template_posix_hook_script,
        "cshell": template_cshell_hook_script,
        "fish": template_fish_hook_script,
        "powershell": template_powershell_hook_script,
        "cmd": template_cmd_hook_script,
        "nushell": template_nushell_hook_script,
        "xonsh": template_xonsh_hook_script,
        "clink-cmd": template_clink_cmd_hook_script,
    }

    hook_script_function = hook_scripts_dict.get(shell_family, None)

    if hook_script_function is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return hook_script_function()


def render_insert_block_marker_init(shell_family: str):
    comment = COMMENT_MARKERS[shell_family]
    return f"{comment} {HOOK_MARKER}-init\n"


def render_insert_block_marker_end(shell_family: str):
    comment = COMMENT_MARKERS[shell_family]
    return f"\n{comment} {HOOK_MARKER}-end"


if __name__ == "__main__":
    print("Breakpoint Here")
