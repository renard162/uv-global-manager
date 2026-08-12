from textwrap import dedent


def template_cshell_hook_script() -> str:
    return dedent(r"""
        alias uve 'if ("!:1" == "activate" && "!:2" != "" && "!:2" != "-h" && "!:2" != "--help") then; eval `\uve activate "\!:2" --hook cshell`; else; \uve !\*; endif'
    """).strip()
