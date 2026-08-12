import re
import winreg

from .generator_script import HOOK_LAUNCHER_SCRIPT_NAME, SCRIPT_EXTENSIONS

AUTORUN_KEY = r"Software\Microsoft\Command Processor\AutoRun"


def find_hook_launcher_win_reg() -> tuple[int, int] | None:
    script_name = f"{HOOK_LAUNCHER_SCRIPT_NAME}.{SCRIPT_EXTENSIONS['cmd']}"
    autorun = read_autorun()

    if autorun is None:
        return None

    hook_match = find_hook(
        value=autorun,
        script_name=script_name,
    )

    if hook_match is None:
        return None

    command_start, command_end = hook_match

    context = parse_cmd_structure(value=autorun)

    return get_removal_range(
        value=autorun,
        command_start=command_start,
        command_end=command_end,
        context=context,
    )


def read_autorun() -> str | None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            AUTORUN_KEY,
            access=winreg.KEY_READ,
        ) as key:
            try:
                value, _ = winreg.QueryValueEx(key, None)
            except FileNotFoundError:
                return None

    except FileNotFoundError:
        return None

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    return value


def find_hook(value: str, script_name: str) -> tuple[int, int] | None:
    prefix_match = re.search(
        r"doskey\s+uve\s*=\s*call\s+",
        value,
        flags=re.IGNORECASE,
    )

    if prefix_match is None:
        return None

    command_start = prefix_match.start()
    path_start = prefix_match.end()

    if path_start >= len(value):
        return None

    if value[path_start] != '"':
        return None

    path_end = find_closing_quote(
        value=value,
        start=path_start,
    )

    if path_end is None:
        return None

    path = value[path_start + 1 : path_end].rstrip()

    if not path_ends_with_script(
        path=path,
        script_name=script_name,
    ):
        return None

    suffix_start = path_end + 1

    suffix_match = re.match(
        r"\s+\$\*",
        value[suffix_start:],
    )

    if suffix_match is None:
        return None

    command_end = suffix_start + suffix_match.end()

    return command_start, command_end


def path_ends_with_script(path: str, script_name: str) -> bool:
    path = path.casefold()
    script_name = script_name.casefold()

    return (
        path == script_name
        or path.endswith(f"\\{script_name}")
        or path.endswith(f"/{script_name}")
    )


def find_closing_quote(value: str, start: int) -> int | None:
    escaped = False

    for index in range(start + 1, len(value)):
        char = value[index]

        if escaped:
            escaped = False
            continue

        if char == "^":
            escaped = True
            continue

        if char == '"':
            return index

    return None


def parse_cmd_structure(value: str) -> "RegCmdStructure":
    separators: list[RegSeparator] = []
    groups: list[RegGroup] = []
    group_stack: list[int] = []
    in_quotes = False
    escaped = False
    index = 0

    while index < len(value):
        char = value[index]

        if escaped:
            escaped = False
            index += 1
            continue

        if char == "^":
            escaped = True
            index += 1
            continue

        if char == '"':
            in_quotes = not in_quotes
            index += 1
            continue

        if in_quotes:
            index += 1
            continue

        if char == "(":
            group_index = len(groups)

            groups.append(
                RegGroup(
                    start=index,
                    end=None,
                    parent=(group_stack[-1] if group_stack else None),
                )
            )

            group_stack.append(group_index)

            index += 1
            continue

        if char == ")":
            if group_stack:
                group_index = group_stack.pop()
                groups[group_index].end = index

            index += 1
            continue

        if char == "&":
            separator_start = index

            if index + 1 < len(value) and value[index + 1] == "&":
                separator_end = index + 2
            else:
                separator_end = index + 1

            separators.append(
                RegSeparator(
                    start=separator_start,
                    end=separator_end,
                    depth=len(group_stack),
                    group=(groups[group_stack[-1]] if group_stack else None),
                )
            )

            index = separator_end
            continue

        if char == "|" and index + 1 < len(value) and value[index + 1] == "|":
            separator_start = index
            separator_end = index + 2

            separators.append(
                RegSeparator(
                    start=separator_start,
                    end=separator_end,
                    depth=len(group_stack),
                    group=(groups[group_stack[-1]] if group_stack else None),
                )
            )

            index = separator_end
            continue

        index += 1

    return RegCmdStructure(
        separators=separators,
        groups=groups,
    )


def get_removal_range(
    value: str,
    command_start: int,
    command_end: int,
    context: "RegCmdStructure",
) -> tuple[int, int]:
    group = get_innermost_group(
        groups=context.groups,
        start=command_start,
        end=command_end,
    )

    previous_separator = get_previous_separator(
        separators=context.separators,
        command_start=command_start,
        group=group,
    )

    next_separator = get_next_separator(
        separators=context.separators,
        command_end=command_end,
        group=group,
    )

    has_previous_command = has_command_before(
        value=value,
        command_start=command_start,
        separator=previous_separator,
        group=group,
    )

    has_next_command = has_command_after(
        value=value,
        command_end=command_end,
        separator=next_separator,
        group=group,
    )

    if group is not None and not has_previous_command and not has_next_command:
        return expand_group_removal_range(
            value=value,
            group=group,
            context=context,
        )

    if has_next_command and next_separator is not None:
        return extend_start_and_end(
            value=value,
            start=command_start,
            end=next_separator.end,
        )

    if has_previous_command and previous_separator is not None:
        return extend_start_and_end(
            value=value,
            start=previous_separator.start,
            end=command_end,
        )

    return extend_start_and_end(
        value=value,
        start=command_start,
        end=command_end,
    )


def get_innermost_group(
    groups: list["RegGroup"],
    start: int,
    end: int,
) -> "RegGroup | None":
    candidates = [
        group
        for group in groups
        if (group.end is not None and group.start < start and end <= group.end)
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda group: group.start,
    )


def get_previous_separator(
    separators: list["RegSeparator"],
    command_start: int,
    group: "RegGroup | None",
) -> "RegSeparator | None":
    candidates = [
        separator
        for separator in separators
        if (
            separator.end <= command_start
            and same_group(
                separator=separator,
                group=group,
            )
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda separator: separator.end,
    )


def get_next_separator(
    separators: list["RegSeparator"],
    command_end: int,
    group: "RegGroup | None",
) -> "RegSeparator | None":
    candidates = [
        separator
        for separator in separators
        if (
            separator.start >= command_end
            and same_group(
                separator=separator,
                group=group,
            )
        )
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda separator: separator.start,
    )


def same_group(separator: "RegSeparator", group: "RegGroup | None") -> bool:
    return separator.group is group


def has_command_before(
    value: str,
    command_start: int,
    separator: "RegSeparator | None",
    group: "RegGroup | None",
) -> bool:
    if separator is None:
        return False

    region_start = group.start + 1 if group is not None else 0

    text = value[region_start : separator.start]

    return bool(text.strip())


def has_command_after(
    value: str,
    command_end: int,
    separator: "RegSeparator | None",
    group: "RegGroup | None",
) -> bool:
    if separator is None:
        return False

    region_end = group.end if group is not None else len(value)
    text = value[separator.end : region_end]

    return bool(text.strip())


def expand_group_removal_range(
    value: str,
    group: "RegGroup",
    context: "RegCmdStructure",
) -> tuple[int, int]:
    start = group.start
    end = group.end + 1

    parent = get_parent_group(
        groups=context.groups,
        group=group,
    )

    previous_separator = get_previous_separator(
        separators=context.separators,
        command_start=start,
        group=parent,
    )

    next_separator = get_next_separator(
        separators=context.separators,
        command_end=end,
        group=parent,
    )

    has_previous = previous_separator is not None
    has_next = next_separator is not None

    if has_next:
        return extend_start_and_end(
            value=value,
            start=start,
            end=next_separator.end,
        )

    if has_previous:
        return extend_start_and_end(
            value=value,
            start=previous_separator.start,
            end=end,
        )

    return extend_start_and_end(
        value=value,
        start=start,
        end=end,
    )


def get_parent_group(groups: list["RegGroup"], group: "RegGroup") -> "RegGroup | None":
    if group.parent is None:
        return None

    return groups[group.parent]


def extend_start_and_end(value: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and value[start - 1].isspace():
        start -= 1

    while end < len(value) and value[end].isspace():
        end += 1

    return start, end


class RegSeparator:
    def __init__(self, start: int, end: int, depth: int, group: "RegGroup | None"):
        self.start = start
        self.end = end
        self.depth = depth
        self.group = group


class RegGroup:
    def __init__(self, start: int, end: int | None, parent: int | None):
        self.start = start
        self.end = end
        self.parent = parent


class RegCmdStructure:
    def __init__(self, separators: list[RegSeparator], groups: list[RegGroup]):
        self.separators = separators
        self.groups = groups
