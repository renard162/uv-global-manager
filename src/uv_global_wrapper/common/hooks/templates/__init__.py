from .cmd import template_cmd_hook_script
from .cshell import template_cshell_hook_script
from .fish import template_fish_hook_script
from .nushell import template_nushell_hook_script
from .posix import template_posix_hook_script
from .powershell import template_powershell_hook_script
from .xonsh import template_xonsh_hook_script

__all__ = [
    "template_cmd_hook_script",
    "template_cshell_hook_script",
    "template_fish_hook_script",
    "template_nushell_hook_script",
    "template_posix_hook_script",
    "template_powershell_hook_script",
    "template_xonsh_hook_script",
]
