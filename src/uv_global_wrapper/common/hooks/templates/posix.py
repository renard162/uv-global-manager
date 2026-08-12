from textwrap import dedent


def template_posix_hook_script() -> str:
    return dedent("""
        uve() {
            if [ "$1" = "activate" ] &&
            [ -n "$2" ] &&
            [ "$2" != "-h" ] &&
            [ "$2" != "--help" ]; then

                activation_command="$(command uve activate "$2" --hook posix)" || return 1

                eval "$activation_command"
                return $?
            fi

            command uve "$@"
        }
    """).strip()
