# python-scaffold

Describe your project here.

## Installation

### mise-en-place

```zsh
brew install mise
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc
source ~/.zshrc
```

## Setup

```zsh
mise trust
task init
```

## Enable logger

To enable logger, place `.env` on project root

```properties:.env
LOG_LEVEL=INFO
LOG_DIR=/path/to/log/dir
TZ=Asia/Tokyo
```
