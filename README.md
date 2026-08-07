# UV Wrapper for Global Virtual Environments

# VERSÃO ANTIGA, BASEADA EM SCRIPTS, REFAZER README APÓS TERMINADO DESENVOLVIMENTO BASE

> **Bring the convenience of global virtual environments to the speed and simplicity of UV.**

While UV is an outstanding tool for project-oriented Python development, many developers still rely on reusable global virtual environments for experimentation, automation, personal tooling, and utility applications.

This wrapper extends UV with a familiar workflow for creating and managing global virtual environments, allowing you to maintain isolated Python installations that are independent of any specific project.

Instead of creating a new environment for every experiment, you can build a collection of reusable environments, each tailored for a different purpose, while still benefiting from UV's performance and dependency management.

When an experiment evolves into a real project, you can seamlessly bootstrap a new standard UV project from your currently active global environment. This lets you carry over an already configured Python version and toolset, making it easy to transition from quick experimentation to a dedicated, project-oriented workflow without starting from scratch.


---

## Why Global Virtual Environments?

Project-specific environments are the recommended approach for software development, but they are not always the most practical solution.

Many everyday tasks do not belong to a dedicated project:

- Testing new Python libraries.
- Running utility scripts.
- Experimenting with new technologies.
- Maintaining automation tools.
- Keeping separate environments for different Python versions.
- Creating specialized environments with pre-installed applications such as Spyder, Jupyter, or scientific libraries.

For example, you might want a permanent environment dedicated to Spyder, providing a workflow similar to MATLAB, another one for data science experiments, and another one for automation scripts. Each environment remains fully isolated from your system Python while being immediately reusable whenever needed.

This wrapper makes that workflow straightforward by managing global virtual environments powered by UV.

---

# Features

- Create reusable global virtual environments.
- Activate existing environments with a single command.
- List all managed environments.
- Remove environments when they are no longer needed.
- Create new UV projects that automatically use the currently active global environment.
- Preserve the speed and dependency management of UV while adding a convenient global workflow.

---

# Available Commands

All wrapper commands provide built-in help through the standard `-h` or `--help` options, which display detailed usage information, available arguments, and examples.

The wrapper is designed to work seamlessly from the Windows Command Prompt (CMD), Windows PowerShell 5.1 or later, and Bash on Windows (such as Git Bash), allowing you to use the same commands regardless of your preferred shell.

---

## `uv-mkvenv`

Creates a new global virtual environment managed by the wrapper.

Use this command whenever you need a reusable environment for experimentation, personal tooling, or long-lived utilities.

---

## `uv-rmvenv`

Deletes a global virtual environment previously created by the wrapper.

Only environments managed by the wrapper are affected, leaving any unrelated Python environments untouched.

---

## `uv-workon`

Lists all global virtual environments managed by the wrapper.

When an environment name is provided, the command activates that environment, making it immediately available for use.

This provides a workflow similar to the well-known `workon` command from virtualenvwrapper, while using UV as the underlying engine.

---

## `uv-createproject`

Creates a new project following the standard UV project layout using the currently active global virtual environment.

This makes it easy to turn an experiment into a dedicated project by bootstrapping a new UV project from an environment that is already configured with the desired Python version and tooling.

---

## `uv-setup-wrapper`

Initializes or restores the wrapper's internal directory structure.

This command is executed automatically whenever one of the wrapper commands is invoked, ensuring that the required directories are always available. It can also be run manually with the appropriate option to recreate the wrapper's directory structure as if it had just been installed, without affecting any existing global virtual environments. This makes it useful for recovering from accidental modifications or other local issues without requiring a full reinstallation.

---

# Why Use This Wrapper?

UV was designed with a strong focus on project-based development, making it an excellent choice for managing modern Python projects.

At the same time, many developers still prefer keeping a few reusable global virtual environments for tasks that are not tied to a specific project. They are convenient for trying out new libraries, running personal scripts, maintaining development tools, or working with applications that benefit from a permanent environment.

This wrapper complements that workflow by bringing the convenience of global virtual environments to UV. You can create, manage, and reuse isolated environments for everyday work, and when an experiment eventually becomes a real project, you can easily bootstrap a standard UV project from the environment you have already configured.

If you regularly switch between small experiments, automation scripts, and full projects, this wrapper helps reduce repetitive setup while preserving the workflow and performance that make UV appealing.
