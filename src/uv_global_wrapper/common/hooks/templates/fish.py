from textwrap import dedent


def template_fish_hook_script() -> str:
    return dedent("""
        function uve
            if test (count $argv) -ge 2
                if test "$argv[1]" = "activate"
                    if test "$argv[2]" != "-h"; and test "$argv[2]" != "--help"
                        set -l activation_command (command uve activate "$argv[2]" --hook fish)
                        or return $status

                        eval $activation_command
                        return $status
                    end
                end
            end

            command uve $argv
        end
    """).strip()
