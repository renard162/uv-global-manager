from textwrap import dedent


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
                    ["uve", "activate", *args[1:], "--hook", "xonsh"],
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
