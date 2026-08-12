from textwrap import dedent


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
                $activation_command = & $uve_command activate $args[1] --hook powershell

                if ($LASTEXITCODE -ne 0) {
                    return
                }

                Invoke-Expression $activation_command
                return
            }

            & $uve_command @args
        }
    """).strip()
