from textwrap import dedent

from shellingham import ShellDetectionFailure

from .utils import (
    hook_script_path,
    path_as_posix,
    path_as_windows,
    venv_script_folder_name,
    venvs_root_path,
)


def gen_shell_hook_call(shell_family: str) -> str:
    hook_script_location = hook_script_path(abs_path=False)
    posix_location = path_as_posix(hook_script_location)
    windows_location = path_as_windows(hook_script_location)

    hook_calls_dict = {
        "posix": f'source "$HOME/{posix_location}/uvg-posix.sh"',
        "cshell": f'source "$HOME/{posix_location}/uvg-cshell.csh"',
        "fish": f'source "$HOME/{posix_location}/uvg-fish.fish"',
        "powershell": f'. "$HOME\\{windows_location}\\uvg-powershell.ps1"',
        "cmd": f'doskey uvg=call "%USERPROFILE%\\{windows_location}\\uvg-cmd.bat" $*',
        "nushell": f'source ($nu.home-dir | path join "{posix_location}/uvg-nushell.nu")',
        "xonsh": f'source "$HOME/{posix_location}/uvg-xonsh.xsh"',
    }

    hook_call = hook_calls_dict.get(shell_family, None)

    if hook_call is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return hook_call


def gen_shell_hook_script(shell_family: str) -> str:
    hook_scripts_dict = {
        "posix": gen_posix_hook_script,
        "cshell": gen_cshell_hook_script,
        "fish": gen_fish_hook_script,
        "powershell": gen_powershell_hook_script,
        "cmd": gen_cmd_hook_script,
        "nushell": gen_nushell_hook_script,
        "xonsh": gen_xonsh_hook_script,
    }

    hook_script_function = hook_scripts_dict.get(shell_family, None)

    if hook_script_function is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return hook_script_function()


def gen_posix_hook_script() -> str:
    return dedent("""
        uvg() {
            if [ "$1" = "activate" ] &&
               [ -n "$2" ] &&
               [ "$2" != "-h" ] &&
               [ "$2" != "--help" ]; then

                activation_command="$(command uvg activate "$2")" || return 1

                eval "$activation_command"
                return $?
            fi

            command uvg "$@"
        }
    """).strip()


def gen_cshell_hook_script() -> str:
    return dedent(r"""
        alias uvg 'if ("\!:1" == "activate" && "\!:2" != "" && "\!:2" != "-h" && "\!:2" != "--help") then; eval `\uvg activate "\!:2"`; else; \uvg \!*; endif'
    """).strip()


def gen_fish_hook_script() -> str:
    return dedent("""
        function uvg
            if test (count $argv) -ge 2
                if test "$argv[1]" = "activate"
                    if test "$argv[2]" != "-h"; and test "$argv[2]" != "--help"
                        set -l activation_command (command uvg activate "$argv[2]")
                        or return $status

                        eval $activation_command
                        return $status
                    end
                end
            end

            command uvg $argv
        end
    """).strip()


def gen_powershell_hook_script() -> str:
    return dedent("""
        $uvg_command = (Get-Command uvg -CommandType Application).Source

        function uvg {
            if (
                $args.Count -ge 2 -and
                $args[0] -eq "activate" -and
                $args[1] -ne "-h" -and
                $args[1] -ne "--help"
            ) {
                $activation_command = & $uvg_command activate $args[1]

                if ($LASTEXITCODE -ne 0) {
                    return
                }

                Invoke-Expression $activation_command
                return
            }

            & $uvg_command @args
        }
    """).strip()


def gen_cmd_hook_script() -> str:
    return dedent(r"""
        @echo off

        if /i "%~1"=="activate" (
            if "%~2"=="" goto :passthrough
            if /i "%~2"=="-h" goto :passthrough
            if /i "%~2"=="--help" goto :passthrough

            for /f "delims=" %%A in (
                'uvg.exe activate "%~2"'
            ) do call %%A

            exit /b %errorlevel%
        )

        :passthrough
        uvg.exe %*
    """).strip()


def gen_nushell_hook_script() -> str:
    root_folder = path_as_posix(venvs_root_path(abs_path=False))
    script_folder = venv_script_folder_name()
    return dedent(f"""
        def --env deactivate [] {{
            if "UVG_OLD_PATH" not-in $env {{
                return
            }}

            load-env {{
                PATH: $env.UVG_OLD_PATH
                PROMPT_COMMAND: $env.UVG_OLD_PROMPT_COMMAND
            }}

            hide-env VIRTUAL_ENV
            hide-env VIRTUAL_ENV_PROMPT
            hide-env UVG_OLD_PATH
            hide-env UVG_OLD_PROMPT_COMMAND
            hide-env VIRTUAL_PREFIX
        }}

        def --env uvg-activate [venv_name: string] {{
            if "UVG_OLD_PATH" in $env {{
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
                UVG_OLD_PATH: $old_path
                UVG_OLD_PROMPT_COMMAND: $old_prompt_command
                VIRTUAL_ENV: ($venv_path | into string)
                VIRTUAL_ENV_PROMPT: $venv_name
                VIRTUAL_PREFIX: $virtual_prefix
                PROMPT_COMMAND: $new_prompt
                PATH: ($old_path | prepend $scripts_path)
            }}
        }}

        def --env uvg [...args] {{
            if (
                ($args | length) >= 2 and
                $args.0 == "activate" and
                $args.1 != "-h" and
                $args.1 != "--help"
            ) {{
                try {{
                    ^uvg ...$args | ignore
                }} catch {{
                    return
                }}

                uvg-activate $args.1
                return
            }}

            ^uvg ...$args
        }}
    """).strip()


def gen_xonsh_hook_script() -> str:
    return dedent("""
        import subprocess
        import sys

        def _uvg(args):
            if (
                len(args) >= 2
                and args[0] == "activate"
                and args[1] not in ("-h", "--help")
            ):
                result = subprocess.run(
                    ["uvg", "activate", *args[1:]],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(result.stderr, end="", file=sys.stderr)
                    return result.returncode

                __xonsh__.execer.exec(result.stdout)
                return 0

            return subprocess.run(["uvg", *args]).returncode

        __xonsh__.aliases["uvg"] = _uvg
    """).strip()


if __name__ == "__main__":
    print(__name__)
