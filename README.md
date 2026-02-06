# QueryTune

QueryTune is a native macOS application designed to optimize SQL queries using Large Language Models (LLMs). It supports both **local models** (via Ollama) and **cloud services** (via OpenAI), providing developers and DBAs with a powerful tool to refactor SQL code, suggest indices, and improve database performance.

## 🚀 Features

- **Dual Analysis Modes:**
  - **Optimize:** Generates structured results including a refactored query, index suggestions, and technical explanations.
  - **Chat Mode:** Provides a conversational, streaming experience (word-by-word) for general query analysis and brainstorming.
- **Context Awareness:** Add specific instructions, table sizes, or schema details in the collapsible "Context" area to improve AI accuracy.
- **Hybrid AI Processing:** 
  - **Local:** Connects to your local Ollama instance (100% private).
  - **Cloud:** Full support for OpenAI (GPT-4o, etc.) or any OpenAI-compatible API (Groq, LM Studio).
- **Settings Persistence:** Remembers your preferred Model, Database Type, Theme, API Keys, and Font settings.
- **Native macOS Experience:** Clean interface with dark mode support, native menus (About/Preferences), and optimized build for Apple Silicon and Intel.

## 🛠 Technical Stack

- **Language:** Python 3.13
- **GUI Framework:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **AI Backend:** OpenAI-compatible API (Ollama v1, OpenAI API, etc.)
- **Packaging:** PyInstaller + `create-dmg`

## 📦 Getting Started

### Prerequisites

1.  **AI Provider:** 
    - **Local:** Install [Ollama](https://ollama.com/) and pull a model (e.g., `ollama pull qwen2.5-coder:7b`).
    - **Cloud:** Obtain an API Key from [OpenAI](https://platform.openai.com/).
2.  **Python & Tkinter:**
    ```bash
    brew install python@3.13 python-tk@3.13
    ```

### Development Setup

1.  **Clone the repository and install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the application:**
    ```bash
    python main.py
    ```

### Packaging for macOS

To create a standalone `.app` and a `.dmg` installer:
```bash
./build_macos.sh
```

## 🏗 Roadmap

- [ ] **DDL Integration:** Automatic schema parsing from SQL files to provide even more context.
- [ ] **History Log:** Save and browse previous optimizations.
- [ ] **Visual Diff:** Side-by-side comparison between original and optimized queries.

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
