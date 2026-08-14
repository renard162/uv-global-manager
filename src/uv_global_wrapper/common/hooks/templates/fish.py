from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_fish_hook_script() -> str:
    commands = " ".join(COMMANDS_DICT.values())
    venvs_path = path_as_posix(venvs_root_path(abs_path=False))

    return dedent(
        f"""
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

        complete -c uve -f -n "__fish_use_subcommand" -a "{commands}"

        complete -c uve -f \
            -n "__fish_seen_subcommand_from help" \
            -a "{commands}"

        complete -c uve -f \
            -n "__fish_seen_subcommand_from activate delete" \
            -a '(for environment in "$HOME/{venvs_path}"/*
                    if test -d "$environment"
                        basename "$environment"
                    end
                end)'
        """
    ).strip()
