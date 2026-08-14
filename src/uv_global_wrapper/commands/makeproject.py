from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

from ..common.paths import (
    active_venv_path,
    venv_interpreter_path,
)
from ..common.repository import (
    EXTERNAL_PACKAGES,
    check_package_call,
    download_package,
    run_package,
)
from ..common.utils import (
    parse_pyvenv_cfg,
    print_stderr,
)


def register(subparsers):
    parser = subparsers.add_parser(
        "make-project",
        help="Generate a UV project template from the active virtual environment.",
        description=(
            "Generate a UV project template from the active virtual environment, "
            "including its project dependencies."
        ),
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Project type:
    Choose one of --app, --lib, --package, or --no-package to define the type
    and structure of the project. These options are mutually exclusive.

    If none of these options is provided, --package is used by default.
    Use --app for an application project, --lib for a library project,
    --package to create a project configured as a Python package, or
    --no-package to create a project without package support.

    See "uv help init" for more details about these project types.

Examples:
    uve make-project
    uve make-project myproject
    uve make-project myproject --bare
    uve make-project myproject --app
    uve make-project myproject --lib
    uve make-project myproject --package
    uve make-project myproject --no-package
    uve make-project myproject --vcs git
    uve make-project myproject --vcs none
    uve make-project myproject --build-backend uv
    uve make-project myproject --build-backend hatch
    uve make-project myproject --bounds lower
    uve make-project myproject --bounds major
    uve make-project myproject --bounds minor
    uve make-project myproject --bounds exact
""",
    )

    parser.add_argument(
        "name",
        nargs="?",
        metavar="NAME",
        help="Project name. The project directory is created using this name.",
    )

    parser.add_argument(
        "--vcs",
        choices=("git", "none"),
        default=None,
        metavar="VCS",
        help=(
            "Initialize a version control system for the project. "
            "Valid choices are git and none. "
            "See 'uv help init' for more information."
        ),
    )

    parser.add_argument(
        "--build-backend",
        choices=(
            "uv",
            "hatch",
            "flit",
            "pdm",
            "poetry",
            "setuptools",
            "maturin",
            "scikit",
        ),
        default=None,
        metavar="BUILD_BACKEND",
        help=(
            "Initialize a build backend for the project. "
            "Valid choices are uv, hatch, flit, pdm, poetry, setuptools, "
            "maturin, and scikit. "
            "See 'uv help init' for more information."
        ),
    )

    parser.add_argument(
        "--bounds",
        choices=("lower", "major", "minor", "exact"),
        default="exact",
        metavar="BOUNDS",
        help=(
            "Specify the version bounds used for project dependencies. "
            "Valid choices are lower, major, minor, and exact. "
            "Defaults to exact. "
            "See 'uv help add' for more information."
        ),
    )

    project_type = parser.add_mutually_exclusive_group()

    project_type.add_argument(
        "--bare",
        action="store_true",
        help=(
            "Generate only the project metadata and dependency specification.\n"
            "\n"
            "When this option is specified, the project virtual environment "
            "is not created and project dependencies are not installed."
        ),
    )

    project_type.add_argument(
        "--app",
        action="store_const",
        const="--app",
        dest="project_type",
        help="Generate an application project.",
    )

    project_type.add_argument(
        "--lib",
        action="store_const",
        const="--lib",
        dest="project_type",
        help="Generate a library project.",
    )

    project_type.add_argument(
        "--package",
        action="store_const",
        const="--package",
        dest="project_type",
        help="Generate a package project.",
    )

    project_type.add_argument(
        "--no-package",
        action="store_const",
        const="--no-package",
        dest="project_type",
        help="Generate a project without a package.",
    )

    parser.set_defaults(func=makeproject_run, parser=parser)


def makeproject_run(args: argparse.Namespace):
    if args.name is None:
        args.parser.print_help()
        return

    active_env_path = active_venv_path()

    if active_env_path is None:
        raise RuntimeError(
            "This command can only be executed from an active virtual environment."
        )

    env_name = active_env_path.name
    python_path = venv_interpreter_path(env_name)

    if not python_path.is_file():
        raise RuntimeError(
            "Python interpreter for the active virtual environment was not found: "
            f'"{python_path}".'
        )

    project_name = args.name or env_name
    target_path = Path.cwd() / project_name

    if target_path.exists():
        raise FileExistsError(
            f'The destination directory "{target_path}" already exists.'
        )

    try:
        init_project(
            target_path=target_path,
            python_path=python_path,
            bare=args.bare,
            project_type=args.project_type,
            vcs=args.vcs,
            build_backend=args.build_backend,
        )

        requirements_path = target_path / "requirements.txt"

        venv_config = parse_pyvenv_cfg(active_env_path / "pyvenv.cfg")
        implementation = venv_config.get("implementation")

        if implementation is None:
            print_stderr(
                'Warning: The "implementation" key was not found in pyvenv.cfg.'
            )

        use_pip_freeze = implementation != "CPython"

        if not use_pip_freeze:
            use_pip_freeze = not ensure_pipdeptree()

        export_requirements(
            python_path=python_path,
            requirements_path=requirements_path,
            use_pip_freeze=use_pip_freeze,
            bounds=args.bounds,
        )

        add_requirements(
            target_path=target_path,
            requirements_path=requirements_path,
            bare=args.bare,
        )

    except Exception:
        remove_project_folder(target_path)
        raise


def ensure_pipdeptree() -> bool:
    if check_package_call(
        "pipdeptree",
        raise_on_fail=False,
    ):
        return True

    print("Updating the local package repository.")

    if download_package(
        EXTERNAL_PACKAGES["pipdeptree"],
        raise_on_fail=False,
        print_stdout=True,
        print_stderr=False,
    ):
        print_stderr(
            "Error: Failed to update the local package repository. "
            'Falling back to "uv pip freeze".'
        )
        return False

    if check_package_call(
        "pipdeptree",
        raise_on_fail=False,
    ):
        return True

    print_stderr(
        "Warning: The local package repository is unavailable. "
        'Falling back to "uv pip freeze".'
    )

    return False


def init_project(
    target_path: Path,
    python_path: Path,
    bare: bool,
    project_type: str | None,
    vcs: str | None,
    build_backend: str | None,
) -> None:
    command = [
        "uv",
        "init",
        "--python",
        str(python_path),
    ]

    if bare:
        command.append("--bare")

    if project_type is not None:
        command.append(project_type)

    if vcs is not None:
        command.extend(["--vcs", vcs])

    if build_backend is not None:
        command.extend(["--build-backend", build_backend])

    command.append(str(target_path))

    try:
        subprocess.run(
            command,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("uv init failed.") from exc


def apply_bounds(
    requirements: str,
    bounds: str,
) -> str:
    if bounds == "exact":
        return requirements

    result = []
    errors = []

    for line in requirements.splitlines(keepends=True):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            result.append(line)
            continue

        match = re.fullmatch(
            r"(?P<package>[A-Za-z0-9][A-Za-z0-9._-]*"
            r"(?:\[[^\]]+\])?)"
            r"=="
            r"(?P<version>\d+(?:\.\d+)+)"
            r"(?P<suffix>\s*(?:;.*)?)"
            r"(?P<newline>\r?\n)?",
            line,
        )

        if match is None:
            result.append(line)
            errors.append(line)
            continue

        package = match.group("package")
        version = match.group("version")
        suffix = match.group("suffix")
        newline = match.group("newline") or ""

        try:
            version_parts = [int(part) for part in version.split(".")]

            if bounds == "lower":
                requirement = f"{package}>={version}"

            elif bounds == "major":
                major = version_parts[0]
                upper_bound = f"{major + 1}.0.0"
                requirement = f"{package}>={version},<{upper_bound}"

            else:  # bounds == "minor"
                major = version_parts[0]
                minor = version_parts[1]
                upper_bound = f"{major}.{minor + 1}.0"
                requirement = f"{package}>={version},<{upper_bound}"

        except (ValueError, IndexError):
            result.append(line)
            errors.append(line)
            continue

        result.append(f"{requirement}{suffix}{newline}")

    if errors:
        print_stderr(
            "The following requirements could not be processed. "
            'Their versions were kept as "exact":'
        )
        print_stderr("".join(errors).rstrip())

    return "".join(result)


def export_requirements(
    python_path: Path,
    requirements_path: Path,
    use_pip_freeze: bool,
    bounds: str,
) -> None:
    if use_pip_freeze:
        export_with_pip_freeze(
            python_path=python_path,
            requirements_path=requirements_path,
            bounds=bounds,
        )
        return

    pipdeptree_success = export_with_pipdeptree(
        requirements_path=requirements_path,
        bounds=bounds,
    )
    if not pipdeptree_success:
        export_with_pip_freeze(
            python_path=python_path,
            requirements_path=requirements_path,
            bounds=bounds,
        )


def export_with_pipdeptree(
    requirements_path: Path,
    bounds: str,
) -> bool:
    result = run_package(
        "pipdeptree --warn fail --depth 0 --output freeze",
        raise_on_fail=False,
    )

    if result == 1:
        print_stderr(
            "Error: An error occurred while determining first-level dependencies."
        )
        return False

    result = apply_bounds(
        requirements=str(result),
        bounds=bounds,
    )

    requirements_path.write_text(
        result,
        encoding="utf-8",
    )

    return True


def export_with_pip_freeze(
    python_path: Path,
    requirements_path: Path,
    bounds: str,
) -> None:
    print_stderr(
        "Warning: The generated project may include transitive dependencies "
        "that are not directly required by the project."
    )

    try:
        result = subprocess.run(
            [
                "uv",
                "pip",
                "freeze",
                "--python",
                str(python_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("uv pip freeze failed.") from exc

    requirements = apply_bounds(
        requirements=result.stdout,
        bounds=bounds,
    )

    requirements_path.write_text(
        requirements,
        encoding="utf-8",
    )


def has_requirements(requirements_path: Path) -> bool:
    return any(
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
    )


def add_requirements(
    target_path: Path,
    requirements_path: Path,
    bare: bool,
) -> None:
    if not has_requirements(requirements_path):
        return

    command = [
        "uv",
        "add",
        "--project",
        str(target_path),
    ]

    if bare:
        command.extend(
            [
                "--active",
                "--no-sync",
            ]
        )

        subprocess.run(
            [
                *command,
                "--requirements",
                str(requirements_path),
            ],
            check=True,
        )
        return

    old_virtual_env = os.environ.pop("VIRTUAL_ENV", None)
    try:
        subprocess.run(
            [
                *command,
                "--requirements",
                str(requirements_path),
            ],
            check=True,
        )
    finally:
        if old_virtual_env is not None:
            os.environ["VIRTUAL_ENV"] = old_virtual_env


def remove_project_folder(target_path: Path) -> None:
    if not target_path.exists():
        return

    try:
        shutil.rmtree(target_path)
    except OSError as exc:
        print_stderr(
            f'Error: Unable to delete the project directory "{target_path}": {exc}'
        )
