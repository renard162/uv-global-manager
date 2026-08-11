from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
from pathlib import Path

from ..common.paths import (
    venv_interpreter_path,
    venv_script_path,
    venvs_root_path,
)
from ..common.utils import print_stderr


def register(subparsers):
    parser = subparsers.add_parser(
        "create",
        help="Create a global virtual environment.",
        description="Creates a global virtual environment.",
        formatter_class=argparse.RawTextHelpFormatter,
        allow_abbrev=False,
    )

    parser.add_argument(
        "name",
        nargs="?",
        help="Name of the virtual environment to create.",
    )

    parser.add_argument(
        "-p",
        "--python",
        metavar="PYTHON",
        help=(
            "Python interpreter to use for the virtual environment.\n"
            "UV will not look for Python interpreters in virtual environments.\n"
            'See "uv help python" for supported request formats and Python '
            "discovery details."
        ),
    )

    parser.add_argument(
        "-r",
        "--requirements",
        metavar="FILE",
        help="Install dependencies from a requirements file in the new venv.",
    )

    parser.set_defaults(
        func=create_run,
        parser=parser,
    )


def create_run(args: argparse.Namespace):
    if args.name is None:
        args.parser.print_help()
        return

    env_path = venvs_root_path() / args.name

    if (env_path / "pyvenv.cfg").is_file():
        raise RuntimeError(f'Virtual environment "{args.name}" already exists.')

    if env_path.exists():
        raise FileExistsError(
            f'The virtual environment directory "{env_path}" already exists.'
        )

    env_path.parent.mkdir(parents=True, exist_ok=True)
    requirements_path = None

    if args.requirements is not None:
        requirements_path = Path(args.requirements)

        if not requirements_path.is_file():
            raise FileNotFoundError(
                f'Requirements file "{args.requirements}" not found.'
            )

        if not os.access(requirements_path, os.R_OK):
            raise PermissionError(
                f'Requirements file "{args.requirements}" is not accessible.'
            )

    command = ["uv", "venv"]

    if args.python is not None:
        command.extend(["--python", args.python])

    command.append(str(env_path))

    print(f'Creating virtual environment "{args.name}"...')

    try:
        subprocess.run(
            command,
            check=True,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print_stderr("\nError creating the virtual environment.")

        if exc.stderr:
            print_stderr(exc.stderr.rstrip())

        if exc.stderr and exc.stderr.lstrip().startswith("error: No interpreter found"):
            print_stderr(
                'Check that the value passed to "--python" is a valid Python request.'
            )
            print_stderr(
                'Use "uv python list" to see available Python versions available.'
            )

        if env_path.exists():
            shutil.rmtree(env_path)

        raise RuntimeError("uv venv failed.") from exc

    gen_pip_aliases(args.name)

    print("\nVirtual environment created successfully.")
    print(f"Location: {env_path}")

    if requirements_path is not None:
        print("\nInstalling dependencies...")

        python_path = venv_interpreter_path(args.name)

        try:
            subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(python_path),
                    "--requirements",
                    str(requirements_path),
                ],
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            print_stderr("\nError installing dependencies.")

            if env_path.exists():
                shutil.rmtree(env_path)

            raise RuntimeError("uv pip install failed.") from exc

        print("\nDependencies installed successfully.")


def gen_pip_aliases(venv_name: str) -> None:
    scripts_path = venv_script_path(venv_name)
    scripts_path.mkdir(parents=True, exist_ok=True)

    aliases = {
        "": ('#!/usr/bin/env sh\nuv pip "$@"\n'),
        ".csh": ("uv pip $argv:q\n"),
        ".fish": ("uv pip $argv\n"),
        ".ps1": ("uv pip @args\nexit $LASTEXITCODE\n"),
        ".bat": ("@echo off\nuv pip %*\nexit /b %ERRORLEVEL%\n"),
        ".nu": ("uv pip ...$args\n"),
        ".xsh": ("uv pip @(args)\n"),
    }

    for extension, content in aliases.items():
        for name in ("pip", "pip3"):
            script_path = scripts_path / f"{name}{extension}"
            script_path.write_text(content, encoding="utf-8")

            if not extension:
                current_mode = script_path.stat().st_mode
                script_path.chmod(
                    current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                )
