# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
```bash
mise trust
mise i
task init
```

### Common Tasks
- `task init` - Initialize project: installs extensions, dependencies, and pre-commit hooks
- `task update` - Update dependencies and extensions
- `uvx ruff check` - Run linting
- `uvx ruff format` - Format code
- `uvx pyright` - Type checking
- `python main.py` - Run the FastAPI server locally

### Environment Configuration
Create `.env` file in project root for logging:
```
LOG_LEVEL=INFO
LOG_DIR=/path/to/log/dir
TZ=Asia/Tokyo
```

## Architecture

This is a FastAPI-based backend for a think-aloud text modification system that integrates real-time audio transcription with AI-powered text editing.

### Core Components

**WebSocket Flow (`main.py:93`)**
- Real-time audio transcription via OpenAI Whisper API
- Per-user state management with processing flags to prevent concurrent modifications
- Three-phase modification process: judge → plan → apply

**Text Modification Pipeline (`src/usecase/text_modification.py`)**
- `EditPlanGenerator` - Determines if text needs modification and creates edit plan
- `TextModifier` - Applies modifications based on plan and constraints
- `HistorySummarizer` - Maintains context from previous modifications

**Infrastructure Layer**
- `src/infra/gpt/` - GPT client wrappers for different AI tasks
- `src/infra/sounddevice/` - Audio streaming for real-time capture
- `src/infra/ws_transcriber/` - WebSocket client for OpenAI transcription

### State Management
- Global dictionaries manage per-user state: `text_states`, `image_data`, `processing_flags`
- `TextState` tracks original text, current text, modification history, and constraints
- Processing flags prevent concurrent modifications from multiple utterances

### API Endpoints
- `POST /api/display-text` - Initialize text for modification with optional image
- `WebSocket /ws` - Real-time audio processing and text modification
- `POST /api/generate-description` - Generate product descriptions from images

### Key Design Patterns
- Use case layer isolates business logic from infrastructure
- Type definitions in `text_modification_types.py` ensure data consistency
- History summarization maintains context while preventing prompt bloat
- Error handling preserves system state even when individual operations fail