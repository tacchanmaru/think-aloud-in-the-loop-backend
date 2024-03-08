# python-scaffold

Describe your project here.

## Installation

### Rye

Package manager for Python.

```bash
brew install rye
```

### Taplo

Formatter for TOML.

```bash
brew install taplo
```

### Visual Studio Code

```bash
brew install visual-studio-code
```

#### Visual Studio Code Extensions

```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension tamasfe.even-better-toml
code --install-extension esbenp.prettier-vscode
code --install-extension streetsidesoftware.code-spell-checker
```

## Setup

### Rye

```bash
rye sync
```

### Pre-commit

```bash
rye run pre-commit install
```

## Change Python's version

To change your python's version into _3.x_

```bash
rye pin ${3.x}
```

## Add package

To add _python-package_

```bash
rye add ${python-package}
```

## Execute your script

To execute _script/your_script.py_

```bash
rye run execute ${your-script}
```
