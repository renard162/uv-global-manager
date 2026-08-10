import subprocess

from .utils import repository_path

BASE_PYTHON_VERSION = "3.13"


def download_package(
    package: str,
    raise_on_fail: bool = True,
    print_stdout: bool = True,
    print_stderr: bool = False,
) -> int:
    try:
        repository = repository_path()
        subprocess.run(
            [
                "uvx",
                "--python",
                BASE_PYTHON_VERSION,
                "pip",
                "download",
                "--dest",
                str(repository),
                package,
            ],
            stdout=None if print_stdout else subprocess.DEVNULL,
            stderr=None if print_stderr else subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        if not raise_on_fail:
            return 1
        raise RuntimeError(
            f"Failed to download {package} to the local package repository."
        ) from error
    return 0


def check_package_call(
    package: str,
    raise_on_fail: bool = False,
) -> bool:
    repository = repository_path()
    try:
        subprocess.run(
            [
                "uvx",
                "--python",
                BASE_PYTHON_VERSION,
                "--find-links",
                str(repository),
                "--no-index",
                "--offline",
                package,
                "--version",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        if not raise_on_fail:
            return False
        raise RuntimeError(
            f"Package {package} no found in the local package repository."
        ) from error
    return True


def run_package(
    package_and_arguments: str,
    raise_on_fail: bool = True,
    print_stderr: bool = False,
) -> str | int:
    repository = repository_path()
    package_and_arguments_list = package_and_arguments.split()
    package = package_and_arguments_list[0]
    arguments = package_and_arguments_list[1:]
    try:
        result = subprocess.run(
            [
                "uvx",
                "--python",
                BASE_PYTHON_VERSION,
                "--find-links",
                str(repository),
                "--no-index",
                "--offline",
                package,
                *arguments,
            ],
            stdout=subprocess.PIPE,
            stderr=None if print_stderr else subprocess.DEVNULL,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        if not raise_on_fail:
            return 1
        raise RuntimeError(
            f"Failed to run package {package} from the local package repository."
        ) from error
    return result.stdout


if __name__ == "__main__":
    print("__main__")
