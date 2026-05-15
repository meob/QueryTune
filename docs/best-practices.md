# ![Logo](icon_64.png) Best Practices for Context & Tuning

To get the most out of QueryTune, providing the right context to the AI is just as important as choosing the right model.

## 🧠 Recommended Models

| Model Name | Type | Best For | Suggested Temp |
|------------|------|----------|----------------|
| `qwen2.5-coder:7b` | Local | **Default choice.** Balanced speed and excellent SQL logic. | 0.1 |
| `deepseek-r1:8b` | Local | Reasoning-based analysis. Great for deep explanations. | 0.6 |
| `llama3.1:8b` | Local | SQL generation and reliability. | 0.2 |
| `qwen3-coder-next` | Cloud | Top cloud coder, Ollama interface. SQL opt + agentic | 0.2 |
| `gpt-4o` | Cloud | Very fast and reliable generalist for complex tasks. | 0.0 |
| `claude-3.7-sonnet`| Cloud | Exceptional at following complex refactoring rules. | 0.0 |

> **Pro Tip:** For SQL optimization, always keep the temperature low (0.0 - 0.2) to ensure syntactic correctness, except for "Reasoning" models like DeepSeek-R1 which perform better with a slightly higher temperature (0.5 - 0.7).

## 🎯 How to Provide Context

AI models are not psychics; they need to know your database structure to suggest valid optimizations.

### 1. Surgical Context
Provide only the DDL (`CREATE TABLE`) of the tables actually involved in the query. Adding unrelated schemas increases "noise" and the risk of hallucinations.

### 2. Data Statistics
Explicitly state table sizes in the Context area. 
*Example:* `"Table users has 10M rows, Table orders has 500 rows."* 
This is critical for the AI to suggest the correct JOIN order and execution strategy.

### 3. Identify Constraints
Inform the AI about specific limits:
*   *"Do not use window functions (not supported in my DB version)."*
*   *"I cannot add new indexes, only refactor the SQL."*

### 4. Context Window
For long or complex queries, prefer models with at least **32k context** (like Qwen 2.5 or Claude) to avoid the AI "forgetting" the beginning of the prompt.

## 🔐 Privacy Note
**Only local models (via Ollama) guarantee complete privacy.** When using Cloud models (OpenAI, Anthropic), your query and context are sent to their servers. Never include sensitive data or real production secrets in your context.
