# UV Global Environment Manager

<p align="center">
  <a href="https://pypi.org/project/uv-global-manager/">
    <img src="https://img.shields.io/pypi/v/uv-global-manager.svg" alt="Latest PyPI version">
  </a>
  <a href="https://github.com/renard162/uv-global-manager">
    <img src="https://img.shields.io/badge/github-repo-blue?logo=github">
  </a>
</p>

> **Bring the convenience of reusable global environments to the speed and simplicity of UV, with seamless multi-shell and cross-platform support.**

UV provides an excellent project-oriented workflow, but not every Python task needs its own project. This tool brings the convenience of reusable global environments to UV, allowing you to create, manage, and quickly switch between isolated environments for experimentation, automation, utilities, development tools, and other recurring tasks.

Built with native integration for Windows and Linux designed to work across the same shells supported by UV, it provides a consistent workflow without relying on platform-specific scripts. When an experiment grows into a real project, the active environment can also be used as the starting point for a standard UV project, making the transition from experimentation to development straightforward.

---

## Installation

[UV](https://pypi.org/project/uv/) must be installed and available globally through the system `PATH`.

The recommended way to install UV Global Environment Manager is through UV's tool management:

```bash
uv tool install uv-global-manager
```

Once installed, the `uve` command will be available globally.

---

## Why Global Virtual Environments?

Not every Python task needs a dedicated project. Reusable environments are useful whenever you need an isolated, persistent Python environment for a specific purpose.

Many everyday tasks do not belong to a dedicated project:

- Testing new Python libraries.
- Running utility scripts.
- Experimenting with new technologies.
- Maintaining automation tools.
- Building dedicated data science environments.
- Keeping separate environments for different Python versions.
- Creating specialized environments with pre-installed applications such as Spyder, Jupyter, or scientific libraries.

For example, a dedicated environment can provide a Python-based workflow similar to MATLAB by installing Spyder and the required scientific libraries. Other environments can be tailored to any of the use cases above, with each environment remaining fully isolated from the system Python while being immediately available whenever needed.

Reusable environments therefore complement project-specific environments by providing persistent, purpose-built Python installations for tasks that do not require a dedicated project.

---

# Features

- Manage reusable global virtual environments (create, activate, list, and remove).
- Bootstrap standard UV projects from the active environment.
- Support Windows and Linux.
- Support the same shells supported by UV.
- Provide native shell integration across supported platforms.
- Automatically initialize and maintain the required manager infrastructure.

---

# Available Commands

The CLI provides dedicated commands for managing environments, integrating with the current shell, and transitioning from reusable environments to standard UV projects. Run `uve help <command>` to view the complete help, including available options and examples for any command.

---

| Command | Description |
| :------ | :---------- |
| `uve create` | Creates a reusable global virtual environment using any Python version supported by UV. The selected Python version can be downloaded automatically by UV when needed, and dependencies can optionally be installed from a requirements file during creation. |
| `uve list` | Lists managed environments and provides filtering and inspection options, including Python implementation, version, size, and environment statistics. |
| `uve activate` | Activates a managed environment in the current shell using the appropriate shell integration, making its Python interpreter and installed tools immediately available. |
| `uve delete` | Removes a managed environment, with protection against deleting the environment currently in use. |
| `uve make-project` | Bootstraps a standard UV project from the currently active global environment, carrying its Python configuration and dependencies into the new project while allowing the resulting project to be customized through UV's project options. |
| `uve setup` | Configures the manager and its shell integration, with automatic setup available for normal installations and additional resources for users who prefer to perform the setup manually. |

---
