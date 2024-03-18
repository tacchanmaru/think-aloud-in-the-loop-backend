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

## Setup

### First Sync

```bash
rye sync
```

### Pre-commit

```bash
rye run pre-commit install
```

## Change Python's version

To change your python's version into *3.x*

```bash
rye pin <3.x>
rye sync
```

## Add package

To add *python-package*

```bash
rye add <python-package>
rye sync
```

## Execute your script

To execute *script/your_script.py*

```bash
rye run execute <your-script>
```
