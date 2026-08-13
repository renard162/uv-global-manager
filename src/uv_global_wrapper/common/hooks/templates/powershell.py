from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_windows,
    venvs_root_path,
)


def template_powershell_hook_script() -> str:
    commands = " ".join(COMMANDS_DICT.values())
    venvs_path = path_as_windows(venvs_root_path(abs_path=False))

    return dedent(f"""
        $uve_command = (Get-Command uve -CommandType Application).Source

        function uve {{
            param(
                [Parameter(ValueFromRemainingArguments)]
                [ArgumentCompleter({{
                    param(
                        $commandName,
                        $parameterName,
                        $wordToComplete,
                        $commandAst,
                        $fakeBoundParameters
                    )

                    $elements = @($commandAst.CommandElements)
                    $arguments = @(
                        $elements |
                            Select-Object -Skip 1 |
                            ForEach-Object Value
                    )

                    if ($arguments.Count -eq 0) {{
                        "{commands}".Split(" ") |
                            Where-Object {{ $_ -like "$wordToComplete*" }} |
                            ForEach-Object {{
                                [System.Management.Automation.CompletionResult]::new(
                                    $_,
                                    $_,
                                    [System.Management.Automation.CompletionResultType]::ParameterValue,
                                    $_
                                )
                            }}

                        return
                    }}

                    if (
                        $arguments.Count -ge 1 -and
                        $arguments[0] -in @("activate", "delete")
                    ) {{
                        $venvsRoot = Join-Path $HOME "{venvs_path}"

                        if (-not (Test-Path -LiteralPath $venvsRoot -PathType Container)) {{
                            return
                        }}

                        Get-ChildItem -LiteralPath $venvsRoot -Directory |
                            Where-Object {{ $_.Name -like "$wordToComplete*" }} |
                            ForEach-Object {{
                                [System.Management.Automation.CompletionResult]::new(
                                    $_.Name,
                                    $_.Name,
                                    [System.Management.Automation.CompletionResultType]::ParameterValue,
                                    $_.Name
                                )
                            }}
                    }}
                }})]
                [string[]]$Arguments
            )

            if (
                $Arguments.Count -ge 2 -and
                $Arguments[0] -eq "activate" -and
                $Arguments[1] -ne "-h" -and
                $Arguments[1] -ne "--help"
            ) {{
                $activation_command = & $uve_command activate $Arguments[1] --hook powershell

                if ($LASTEXITCODE -ne 0) {{
                    return
                }}

                Invoke-Expression $activation_command
                return
            }}

            & $uve_command @Arguments
        }}
    """).strip()
