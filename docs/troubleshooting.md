# ![Logo](icon_64.png) Setup & Troubleshooting

## Connecting an AI Provider

QueryTune doesn't include an LLM; it connects to a provider of your choice.

### Local: Ollama (Recommended)
1.  Download and install [Ollama](https://ollama.com/).
2.  Open your terminal and pull a model: `ollama pull qwen2.5-coder:7b`.
3.  Ensure Ollama is running (check the menu bar icon).
4.  In QueryTune Settings, the default URL `http://localhost:11434/v1/chat/completions` should work out of the box.

### Cloud: OpenAI or Compatible
1.  Obtain an API Key from your provider (OpenAI, Groq, DeepSeek).
2.  In QueryTune Settings, set the **API URL** provided by the service.
3.  Enter your **API Key**.
4.  Enter the exact **Model Name** (e.g., `gpt-4o`).

> There are several QueryTune parameters you can change. 
> Do you want QueryTune replies in your language? Modify the Chat Prompt in Settings, System Prompt


## Common Issues

### "It takes a long time..."
*   **Optimize Mode:** When QueryTune is used in Optimize Mode it has to finish the whole conversation with AI and this can take a couple of minutes. For a real-time experience use **Chat Mode**.

### "Connection Error"
*   **Local:** Is Ollama running? Can you access `http://localhost:11434` in your browser?
*   **Cloud:** Is your API key correct? Do you have enough credits in your account?
*   **Network:** Check if a firewall is blocking QueryTune.

### "Model Not Found"
*   Ensure the model name in Settings matches exactly what you have in Ollama (run `ollama list` to check).
*   For Cloud, ensure the model name is supported by your API key.

### UI looks weird or Fonts are missing
*   QueryTune uses system fonts (`Menlo`, `Consolas`, `Ubuntu`). If the UI looks misaligned, try changing the font size in Settings.
