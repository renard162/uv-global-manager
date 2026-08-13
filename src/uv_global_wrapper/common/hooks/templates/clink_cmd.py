from textwrap import dedent

from ....commands import COMMANDS_DICT
from ...paths import (
    path_as_posix,
    venvs_root_path,
)


def template_clink_cmd_hook_script() -> str:
    return dedent(r"""
        local function run_uve_hook(command)
            local pipe = io.popen(command, "r")

            if not pipe then
                return nil
            end

            local output = pipe:read("*a")
            pipe:close()

            output = output:gsub("^%s+", ""):gsub("%s+$", "")

            if output == "" then
                return nil
            end

            return output
        end


        local function is_uve_command(line_state)
            local command_index = line_state:getcommandwordindex()
            local command = line_state:getword(command_index)

            return command ~= nil and command:lower() == "uve"
        end


        local function handle_uve(line)
            local commands = clink.parseline(line)

            if #commands ~= 1 then
                return nil
            end

            local line_state = commands[1].line_state

            if not is_uve_command(line_state) then
                return nil
            end

            local command_index = line_state:getcommandwordindex()

            if line_state:getwordcount() < command_index + 2 then
                return nil
            end

            local subcommand = line_state:getword(command_index + 1)

            if subcommand == nil or subcommand:lower() ~= "activate" then
                return nil
            end

            local venv = line_state:getword(command_index + 2)

            if venv == nil or venv == "" then
                return nil
            end

            if venv:lower() == "-h" or venv:lower() == "--help" then
                return nil
            end

            local hook_command =
                'uve.exe activate "' .. venv .. '" --hook cmd'

            local output = run_uve_hook(hook_command)

            if output == nil then
                return nil
            end

            return { output }
        end


        clink.onfilterinput(function(line)
            return handle_uve(line)
        end)
    """).strip()
