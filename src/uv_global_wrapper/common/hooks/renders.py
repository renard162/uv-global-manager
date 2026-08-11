from textwrap import dedent

from shellingham import ShellDetectionFailure

from ..paths import (
    hook_script_path,
    path_as_posix,
    path_as_windows,
    venv_script_folder_name,
    venvs_root_path,
)
from .generator import HOOK_SCRIPTS

COMMENT_MARKERS = {
    "posix": "#",
    "cshell": "#",
    "fish": "#",
    "powershell": "#",
    "cmd": "REM",
    "nushell": "#",
    "xonsh": "#",
}


def render_shell_hook_call_insertion(shell_family: str) -> str:
    comment = COMMENT_MARKERS.get(shell_family, None)

    if comment is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return (
        f"{comment} uv-global-wrapper-hook-call-init\n"
        f"{render_shell_hook_call(shell_family)}\n"
        f"{comment} uv-global-wrapper-hook-call-end"
    )


def render_shell_hook_call(shell_family: str) -> str:
    hook_script_location = hook_script_path(abs_path=False)
    posix_location = path_as_posix(hook_script_location)
    windows_location = path_as_windows(hook_script_location)

    hook_script = HOOK_SCRIPTS.get(shell_family)
    hook_calls_dict = {
        "posix": f'source "$HOME/{posix_location}/{hook_script}"',
        "cshell": f'source "$HOME/{posix_location}/{hook_script}"',
        "fish": f'source "$HOME/{posix_location}/{hook_script}"',
        "powershell": f'. "$HOME\\{windows_location}\\{hook_script}"',
        "cmd": f'doskey uve=call "%USERPROFILE%\\{windows_location}\\{hook_script}" $*',
        "nushell": f'source ($nu.home-dir | path join "{posix_location}/{hook_script}")',
        "xonsh": f'source "~/{posix_location}/{hook_script}"',
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
    }

    hook_script_function = hook_scripts_dict.get(shell_family, None)

    if hook_script_function is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return hook_script_function()


def template_posix_hook_script() -> str:
    return dedent("""
        uve() {
            if [ "$1" = "activate" ] &&
            [ -n "$2" ] &&
            [ "$2" != "-h" ] &&
            [ "$2" != "--help" ]; then

                activation_command="$(command uve activate "$2" --hook)" || return 1

                eval "$activation_command"
                return $?
            fi

            command uve "$@"
        }
    """).strip()


def template_cshell_hook_script() -> str:
    return dedent(r"""
        alias uve 'if ("!:1" == "activate" && "!:2" != "" && "!:2" != "-h" && "!:2" != "--help") then; eval `\uve activate "\!:2" --hook`; else; \uve !\*; endif'
    """).strip()


def template_fish_hook_script() -> str:
    return dedent("""
        function uve
            if test (count $argv) -ge 2
                if test "$argv[1]" = "activate"
                    if test "$argv[2]" != "-h"; and test "$argv[2]" != "--help"
                        set -l activation_command (command uve activate "$argv[2]" --hook)
                        or return $status

                        eval $activation_command
                        return $status
                    end
                end
            end

            command uve $argv
        end
    """).strip()


def template_powershell_hook_script() -> str:
    return dedent("""
        $uve_command = (Get-Command uve -CommandType Application).Source

        function uve {
            if (
                $args.Count -ge 2 -and
                $args[0] -eq "activate" -and
                $args[1] -ne "-h" -and
                $args[1] -ne "--help"
            ) {
                $activation_command = & $uve_command activate $args[1] --hook

                if ($LASTEXITCODE -ne 0) {
                    return
                }

                Invoke-Expression $activation_command
                return
            }

            & $uve_command @args
        }
    """).strip()


def template_cmd_hook_script() -> str:
    return dedent(r"""
        @echo off

        if /i "%~1"=="activate" (
            if "%~2"=="" goto :passthrough
            if /i "%~2"=="-h" goto :passthrough
            if /i "%~2"=="--help" goto :passthrough

            for /f "delims=" %%A in (
                'uve.exe activate "%~2" --hook'
            ) do call %%A

            exit /b %errorlevel%
        )

        :passthrough
        uve.exe %*
    """).strip()


def template_nushell_hook_script() -> str:
    root_folder = path_as_posix(venvs_root_path(abs_path=False))
    script_folder = venv_script_folder_name()
    return dedent(f"""
        def --env deactivate [] {{
            if "UVE_OLD_PATH" not-in $env {{
                return
            }}

            load-env {{
                PATH: $env.UVE_OLD_PATH
                PROMPT_COMMAND: $env.UVE_OLD_PROMPT_COMMAND
            }}

            hide-env VIRTUAL_ENV
            hide-env VIRTUAL_ENV_PROMPT
            hide-env UVE_OLD_PATH
            hide-env UVE_OLD_PROMPT_COMMAND
            hide-env VIRTUAL_PREFIX
        }}

        def --env uve-activate [venv_name: string] {{
            if "UVE_OLD_PATH" in $env {{
                deactivate
            }}

            let venv_path = ($nu.home-dir | path join "{root_folder}" $venv_name)
            let scripts_path = ($venv_path | path join "{script_folder}")
            let old_path = $env.PATH

            let old_prompt_command = if "PROMPT_COMMAND" in $env {{
                $env.PROMPT_COMMAND
            }} else {{
                null
            }}

            let virtual_prefix = $"(char lparen)($venv_name)(char rparen) "

            let new_prompt = if $old_prompt_command == null {{
                {{|| $virtual_prefix }}
            }} else if "closure" in ($old_prompt_command | describe) {{
                {{|| $'($virtual_prefix)(do $old_prompt_command)' }}
            }} else {{
                {{|| $'($virtual_prefix)($old_prompt_command)' }}
            }}

            load-env {{
                UVE_OLD_PATH: $old_path
                UVE_OLD_PROMPT_COMMAND: $old_prompt_command
                VIRTUAL_ENV: ($venv_path | into string)
                VIRTUAL_ENV_PROMPT: $venv_name
                VIRTUAL_PREFIX: $virtual_prefix
                PROMPT_COMMAND: $new_prompt
                PATH: ($old_path | prepend $scripts_path)
            }}
        }}

        def --env uve [...args] {{
            if (
                ($args | length) >= 2 and
                $args.0 == "activate" and
                $args.1 != "-h" and
                $args.1 != "--help"
            ) {{
                try {{
                    ^uve activate $args.1 --hook | ignore
                }} catch {{
                    return
                }}

                uve-activate $args.1
                return
            }}

            ^uve ...$args
        }}
    """).strip()


def template_xonsh_hook_script() -> str:
    return dedent("""
        import subprocess
        import sys

        def _uve(args):
            if (
                len(args) >= 2
                and args[0] == "activate"
                and args[1] not in ("-h", "--help")
            ):
                result = subprocess.run(
                    ["uve", "activate", *args[1:], "--hook"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(result.stderr, end="", file=sys.stderr)
                    return result.returncode

                __xonsh__.execer.exec(result.stdout)
                return 0

            return subprocess.run(["uve", *args]).returncode

        __xonsh__.aliases["uve"] = _uve
    """).strip()


if __name__ == "__main__":
    print("Breakpoint Here")
