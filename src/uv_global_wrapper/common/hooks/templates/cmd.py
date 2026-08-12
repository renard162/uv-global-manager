from textwrap import dedent


def template_cmd_hook_script() -> str:
    return dedent(r"""
        @echo off

        if /i "%~1"=="activate" (
            if "%~2"=="" goto :passthrough
            if /i "%~2"=="-h" goto :passthrough
            if /i "%~2"=="--help" goto :passthrough

            for /f "delims=" %%A in (
                'uve.exe activate "%~2" --hook cmd'
            ) do call %%A

            exit /b %errorlevel%
        )

        :passthrough
        uve.exe %*
    """).strip()
