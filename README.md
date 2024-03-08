# python-scaffold

Describe your project here.

## Installation

1. rye

<https://rye-up.com/guide/installation/>

```bash
brew install rye
```

## Change Python's version

```bash
rye pin ${version}
```

## Setup

1. rye

```bash
rye sync
```

2. pre-commit

```bash
rye run pre-commit install
```

## Add package

```bash
rye add ${package}
```

## Execute your script

To execute ${script/your_script.py}

```bash
rye run execute ${your-script}
```
