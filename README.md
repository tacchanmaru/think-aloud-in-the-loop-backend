# python-scaffold

Describe your project here.

## Installation

### rye

Package manager for Python.

```bash
brew install rye
```

### taplo

Formatter for TOML.

```bash
brew install taplo
```

## Change Python's version

To change your python's version into _3.x_

```bash
rye pin ${3.x}
```

## Setup

### rye

```bash
rye sync
```

### pre-commit

```bash
rye run pre-commit install
```

## Add package

```bash
rye add ${package}
```

## Execute your script

To execute _script/your_script.py_

```bash
rye run execute ${your-script}
```
