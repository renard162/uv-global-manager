from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_posix_hook_script() -> str:
    venvs_path = path_as_posix(venvs_root_path(abs_path=False))
    commands = " ".join(COMMANDS_DICT.values())

    return dedent(f"""
        uve() {{
            if [ "$1" = "activate" ] &&
            [ -n "$2" ] &&
            [ "$2" != "-h" ] &&
            [ "$2" != "--help" ]; then

                activation_command="$(command uve activate "$2" --hook posix)" || return 1

                eval "$activation_command"
                return $?
            fi

            command uve "$@"
        }}

        if [ -n "${{BASH_VERSION:-}}" ]; then
            _uve_complete() {{
                local cur="${{COMP_WORDS[COMP_CWORD]}}"

                if [ "${{COMP_CWORD}}" -eq 1 ]; then
                    COMPREPLY=(
                        $(compgen -W "{commands}" -- "$cur")
                    )
                    return
                fi

                if [ "${{COMP_CWORD}}" -eq 2 ] &&
                [ "${{COMP_WORDS[1]}}" = "help" ]; then
                    COMPREPLY=(
                        $(compgen -W "{commands}" -- "$cur")
                    )
                    return
                fi

                if [ "${{COMP_CWORD}}" -ne 2 ]; then
                    return
                fi

                case "${{COMP_WORDS[1]}}" in
                    activate|delete)
                        local venvs_root="$HOME/{venvs_path}"

                        [ -d "$venvs_root" ] || return

                        local environments
                        environments="$(
                            for environment in "$venvs_root"/*; do
                                [ -d "$environment" ] || continue
                                printf '%s\\n' "${{environment##*/}}"
                            done
                        )"

                        COMPREPLY=(
                            $(compgen -W "$environments" -- "$cur")
                        )
                        ;;
                esac
            }}

            complete -o default -o nospace -F _uve_complete uve
        fi
    """).strip()
