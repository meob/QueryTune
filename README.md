# QueryTune

QueryTune is a native macOS application designed to optimize SQL queries using Large Language Models (LLMs). It supports both **local models** (via Ollama) and **cloud services** (OpenAI API compatible), providing developers and DBAs with a powerful tool to refactor SQL code, suggest indices, and improve database performance.

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

    ```
    brew install python@3.13 python-tk@3.13
    ```

### Development Setup

1.  **Clone the repository.**

2.  **Create and activate a virtual environment (recommended):**

    ```
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```
    pip install -r requirements.txt
    ```

4.  **Run the application:**

    ```
    python main.py
    ```

### Packaging for macOS

To create a standalone `.app` and a `.dmg` installer using the current environment:
```bash
./build_macos.sh
```


## 🎶 Tuning

### Recommended Models

Choosing the right LLM is crucial for high-quality optimizations. Below are the tested models compatible with QueryTune:

| Model Name (Ollama/API) | Local | Best For | Suggested Temp |
| :--- | :---: | :--- | :---: |
| `qwen2.5-coder:7b` | **X** | **Default.** Balanced speed and excellent SQL logic. | 0.1 |
| `deepseek-r1:8b` | **X** | Reasoning-based analysis. Great for explanations. | 0.6 |
| `deepseek-r1:14b` | **X** | High-quality reasoning for complex multi-join queries. | 0.6 |
| `gpt-4o` | | Cloud-based, very fast and reliable generalist. | 0.0 |
| `claude-3-5-sonnet` | | Exceptional at following complex refactoring rules. | 0.0 |

> **Pro Tip:** For SQL optimization, always keep the temperature low (0.0 - 0.2) to ensure syntactic correctness, except for "Reasoning" models like DeepSeek-R1 which perform better with slightly higher temperature.

---

## 🏗 Roadmap

- [ ] **DDL Integration:** Automatic schema parsing from SQL files to provide even more context.
- [ ] **History Log:** Save and browse previous optimizations.
- [ ] **Visual Diff:** Side-by-side comparison between original and optimized queries.

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.
