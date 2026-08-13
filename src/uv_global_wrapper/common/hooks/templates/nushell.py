from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venv_script_folder_name,
    venvs_root_path,
)


def template_nushell_hook_script() -> str:
    commands = repr(list(COMMANDS_DICT.values()))
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

        def uve-completer [spans: list<string>] {{
            if ($spans | length) == 2 {{
                return {commands}
            }}

            if ($spans | length) < 3 {{
                return []
            }}

            let subcommand = $spans.1

            if $subcommand not-in ["activate", "delete"] {{
                return []
            }}

            let venvs_root = ($nu.home-dir | path join "{root_folder}")

            if not ($venvs_root | path exists) {{
                return []
            }}

            return (
                ls $venvs_root
                | where type == dir
                | get name
                | path basename
            )
        }}

        @complete uve-completer
        def --env --wrapped uve [...args] {{
            if (
                ($args | length) >= 2 and
                $args.0 == "activate" and
                $args.1 != "-h" and
                $args.1 != "--help"
            ) {{
                try {{
                    ^uve activate $args.1 --hook nushell | ignore
                }} catch {{
                    return
                }}

                uve-activate $args.1
                return
            }}

            ^uve ...$args
        }}
    """).strip()
