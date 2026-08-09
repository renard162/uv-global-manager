from textwrap import dedent

from shellingham import ShellDetectionFailure

from .utils import hook_script_path


def gen_shell_hook_string(shell_family: str) -> str:
    hook_script_location = hook_script_path(abs_path=False)
    posix_location = hook_script_location.as_posix()
    windows_location = posix_location.replace("/", "\\")

    hook_calls_dict = {
        "posix": f'source "$HOME/{posix_location}/uvg-posix.sh"',
        "c_shell": f'source "$HOME/{posix_location}/uvg-cshell.csh"',
        "fish": f'source "$HOME/{posix_location}/uvg.fish"',
        "powershell": f'. "$HOME\\{windows_location}\\uvg-powershell.ps1"',
        "cmd": f'doskey uvg=call "%USERPROFILE%\\{windows_location}\\uvg-cmd.cmd" $*',
        "nushell": f'source "$nu.home-path/{posix_location}/uvg.nu"',
        "xonsh": f'source "$HOME/{posix_location}/uvg.xsh"',
    }

    hook_call = hook_calls_dict.get(shell_family, None)

    if hook_call is None:
        raise ShellDetectionFailure(f"Unsupported shell family: {shell_family}")

    return hook_call


def gen_shell_hook_script(shell_family: str) -> str:
    hook_scripts_dict = {
        "posix": gen_posix_hook_script,
        "c_shell": gen_c_shell_hook_script,
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
            if [ "$1" = "activate" ]; then
                activation_command="$(command uvg activate "$2")" || return 1
                eval "$activation_command"
                return $?
            fi

            command uvg "$@"
        }
    """).strip()


def gen_c_shell_hook_script() -> str:
    return dedent(r"""
        alias uvg 'if ("\!:1" == "activate") then; eval `\uvg activate "\!:2"`; else; \uvg \!*; endif'
    """).strip()


def gen_fish_hook_script() -> str:
    return dedent("""
        function uvg
            if test "$argv[1]" = "activate"
                set -l activation_command (command uvg activate "$argv[2]")
                or return $status

                eval $activation_command
                return $status
            end

            command uvg $argv
        end
    """).strip()


def gen_powershell_hook_script() -> str:
    return dedent("""
        $uvg_command = (Get-Command uvg -CommandType Application).Source

        function uvg {
            if ($args[0] -eq "activate") {
                $activation_command = & $uvg_command activate $args[1]

                if ($LASTEXITCODE -ne 0) {
                    return $LASTEXITCODE
                }

                Invoke-Expression $activation_command
                return $LASTEXITCODE
            }

            & $uvg_command @args
        }
    """).strip()


def gen_cmd_hook_script() -> str:
    return dedent(r"""
        @echo off

        if "%~1"=="activate" (
            for /f "delims=" %%A in (
                'uvg.exe activate "%~2"'
            ) do call %%A

            exit /b %errorlevel%
        )

        uvg.exe %*
    """).strip()


def gen_nushell_hook_script() -> str:
    return dedent("""
        def --env uvg [...args] {
            if ($args | is-empty) {
                ^uvg
                return
            }

            if ($args.0 == "activate") {
                let activation_file = (mktemp)

                ^uvg activate $args.1 | save --force $activation_file
                source $activation_file
                rm $activation_file

                return
            }

            ^uvg ...$args
        }
    """).strip()


def gen_xonsh_hook_script() -> str:
    return dedent("""
        import subprocess

        def _uvg(args):
            if args and args[0] == "activate":
                result = subprocess.run(
                    ["uvg", "activate", *args[1:]],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(result.stderr, end="", file=__import__("sys").stderr)
                    return result.returncode

                __xonsh__.execer.exec(result.stdout)
                return 0

            return subprocess.run(["uvg", *args]).returncode

        __xonsh__.aliases["uvg"] = _uvg
    """).strip()


if __name__ == "__main__":
    print(__name__)
