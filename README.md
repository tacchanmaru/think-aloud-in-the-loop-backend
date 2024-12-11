# python-scaffold

Describe your project here.

## Installation

### Taskfile

```bash
brew install go-task
task install
```

## Setup

### First Sync

```bash
rye sync --no-lock
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

## Enable logger

To enable logger, place `.env` on project root

```properties:.env
LOG_LEVEL=INFO
LOG_DIR=/path/to/log/dir
TZ=Asia/Tokyo
```
