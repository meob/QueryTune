import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import requests
import threading
import json
import platform
import os
import sys
import sqlparse
import webbrowser
from PIL import Image

# Patch for macOS version detection issues on newer/beta releases (e.g., Sequoia, Tahoe)
if platform.system() == "Darwin":
    os.environ['SYSTEM_VERSION_COMPAT'] = '0'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_path, relative_path)

# --- Configuration ---
class AppConfig:
    APP_NAME = "QueryTune"
    VERSION = "0.0.3"
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    TIMEOUT = 180
    
    # AI Options
    AI_TEMPERATURE = 0.1
    AI_CTX_SIZE = 8192
    DEFAULT_SYSTEM_PROMPT_CHAT = "You are an expert {db_type} DBA. Explain the query and suggest improvements."
    
    # UI 
    FONT_MONO = "Menlo"
    FONT_SANS = "Arial"
    SIZE_QUERY = 10      # Smaller for long queries
    SIZE_INDICES = 12    # Standard mono
    SIZE_EXPLANATION = 16 # Larger for readability

    # SQL Formatting Defaults
    SQL_COMMA_FIRST = False
    SQL_INDENT_WIDTH = 2
    SQL_KEYWORD_CASE = "upper"
    SQL_COMPACT_SELECT = False
    
    DB_OPTIONS = ["PostgreSQL", "MySQL", "SQLite", "ClickHouse", "Standard SQL", "Oracle", "MS SQL Server"]
    # We switch to the standard Chat Completion endpoint which is compatible with both Ollama and OpenAI
    OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
    SETTINGS_FILE = os.path.expanduser("~/.querytune_settings.json")

# System settings
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Preferences")
        self.geometry("600x600")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.layout_ui()
        self.load_current_values()

    def layout_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_ai = self.tabview.add("AI Configuration")
        self.tab_prompts = self.tabview.add("System Prompt")
        self.tab_ui = self.tabview.add("Interface & Appearance")
        
        # --- AI Tab ---
        self.tab_ai.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.tab_ai, text="Provider Presets:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.option_provider = ctk.CTkOptionMenu(self.tab_ai, values=["Ollama (Local)", "OpenAI (Cloud)", "Custom"], command=self.on_provider_change)
        self.option_provider.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(self.tab_ai, text="API Endpoint URL:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.entry_url = ctk.CTkEntry(self.tab_ai)
        self.entry_url.grid(row=1, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_ai, text="API Key (Optional):").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.entry_apikey = ctk.CTkEntry(self.tab_ai, show="*")
        self.entry_apikey.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_ai, text="Model Name:").grid(row=3, column=0, sticky="w", padx=10, pady=10)
        self.model_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        self.model_frame.grid(row=3, column=1, sticky="ew", padx=10, pady=10)
        self.model_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_model = ctk.CTkComboBox(self.model_frame, values=[AppConfig.DEFAULT_MODEL])
        self.entry_model.grid(row=0, column=0, sticky="ew")
        
        self.btn_fetch = ctk.CTkButton(self.model_frame, text="↻", width=30, command=self.fetch_ollama_models)
        self.btn_fetch.grid(row=0, column=1, padx=(5, 0))
        
        ctk.CTkLabel(self.tab_ai, text="Temperature (0.0 - 1.0):").grid(row=4, column=0, sticky="w", padx=10, pady=10)
        self.entry_temp = ctk.CTkEntry(self.tab_ai)
        self.entry_temp.grid(row=4, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_ai, text="Context Size (tokens):").grid(row=5, column=0, sticky="w", padx=10, pady=10)
        self.entry_ctx = ctk.CTkEntry(self.tab_ai)
        self.entry_ctx.grid(row=5, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_ai, text="Timeout (seconds):").grid(row=6, column=0, sticky="w", padx=10, pady=10)
        self.entry_timeout = ctk.CTkEntry(self.tab_ai)
        self.entry_timeout.grid(row=6, column=1, sticky="ew", padx=10, pady=10)

        self.btn_test_conn = ctk.CTkButton(self.tab_ai, text="Test Connection", command=self.test_connection, 
                                          fg_color="#2E86C1", hover_color="#2874A6")
        self.btn_test_conn.grid(row=7, column=1, sticky="e", padx=10, pady=10)

        # --- Prompts Tab ---
        self.tab_prompts.grid_columnconfigure(0, weight=1)
        self.tab_prompts.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.tab_prompts, text="Chat Mode System Prompt:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(self.tab_prompts, text="Use {db_type} as placeholder for the selected database type.", font=ctk.CTkFont(size=11, slant="italic")).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
        
        self.text_prompt_chat = ctk.CTkTextbox(self.tab_prompts, height=200)
        self.text_prompt_chat.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        self.btn_reset_prompt = ctk.CTkButton(self.tab_prompts, text="Reset to Default", 
                                              command=self.reset_chat_prompt,
                                              fg_color="#A04000", hover_color="#CA6F1E", width=120)
        self.btn_reset_prompt.grid(row=3, column=0, sticky="e", padx=10, pady=(0, 10))

        # --- UI Tab ---
        self.tab_ui.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.tab_ui, text="Theme:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.option_theme = ctk.CTkOptionMenu(self.tab_ui, values=["System", "Light", "Dark"])
        self.option_theme.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_ui, text="Mono Font (Code):").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.entry_font_mono = ctk.CTkEntry(self.tab_ui)
        self.entry_font_mono.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(self.tab_ui, text="Sans Font (UI):").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.entry_font_sans = ctk.CTkEntry(self.tab_ui)
        self.entry_font_sans.grid(row=2, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.tab_ui, text="Query Font Size:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.entry_size_query = ctk.CTkEntry(self.tab_ui)
        self.entry_size_query.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(self.tab_ui, text="Explanation Font Size:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.entry_size_expl = ctk.CTkEntry(self.tab_ui)
        self.entry_size_expl.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

        # SQL Formatting Frame
        self.format_frame = ctk.CTkFrame(self.tab_ui)
        self.format_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.format_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.format_frame, text="SQL Formatting Preferences", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(self.format_frame, text="Keyword Case:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.option_keyword_case = ctk.CTkOptionMenu(self.format_frame, values=["UPPER", "lower", "Capitalize"])
        self.option_keyword_case.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.format_frame, text="Indent:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.option_indent_width = ctk.CTkOptionMenu(self.format_frame, values=["2 Spaces", "4 Spaces", "8 Spaces"])
        self.option_indent_width.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        self.switch_comma_first = ctk.CTkSwitch(self.format_frame, text="Comma-First Style (, col)")
        self.switch_comma_first.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        self.switch_compact_select = ctk.CTkSwitch(self.format_frame, text="Compact SELECT (One line)")
        self.switch_compact_select.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        # --- Buttons ---
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        self.btn_save = ctk.CTkButton(self.btn_frame, text="Save & Apply", command=self.save_settings)
        self.btn_save.pack(side="right", padx=10)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Cancel", fg_color="#555555", hover_color="#666666", command=self.destroy)
        self.btn_cancel.pack(side="right", padx=10)

    def on_provider_change(self, choice):
        if choice == "Ollama (Local)":
            self.entry_url.delete(0, tk.END)
            self.entry_url.insert(0, "http://localhost:11434/v1/chat/completions")
            # Restore available models from settings if they look like Ollama models
            models = self.parent.settings.get("available_models", [AppConfig.DEFAULT_MODEL])
            self.entry_model.configure(values=models)
            self.entry_model.set("qwen2.5-coder:7b")
        elif choice == "OpenAI (Cloud)":
            self.entry_url.delete(0, tk.END)
            self.entry_url.insert(0, "https://api.openai.com/v1/chat/completions")
            openai_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            self.entry_model.configure(values=openai_models)
            self.entry_model.set("gpt-4o")

    def test_connection(self):
        url = self.entry_url.get().strip()
        api_key = self.entry_apikey.get().strip()
        model = self.entry_model.get().strip()
        
        def run_test():
            self.btn_test_conn.configure(state="disabled", text="Testing...")
            try:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": "say ok"}],
                    "max_tokens": 5
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    tk.messagebox.showinfo("Success", "Connection successful!")
                else:
                    tk.messagebox.showerror("Error", f"Server returned status {response.status_code}: {response.text}")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Connection failed: {e}")
            finally:
                self.btn_test_conn.configure(state="normal", text="Test Connection")

        threading.Thread(target=run_test, daemon=True).start()

    def fetch_ollama_models(self):
        url = self.entry_url.get().strip()
        if "localhost" in url or "127.0.0.1" in url or "/api/" in url or ":11434" in url:
            try:
                import re
                base_url = re.sub(r'/v1/.*', '', url)
                if not base_url.endswith("/api/tags"):
                    base_url = base_url.rstrip("/") + "/api/tags"
                
                response = requests.get(base_url, timeout=5)
                response.raise_for_status()
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    self.entry_model.configure(values=models)
                    self.entry_model.set(models[0])
                else:
                    tk.messagebox.showinfo("Ollama", "No models found on this Ollama instance.")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Could not fetch models from Ollama: {e}")
        else:
            tk.messagebox.showinfo("Notice", "Model fetching is only available for local Ollama instances.")

    def load_current_values(self):
        s = self.parent.settings
        
        self.option_provider.set("Custom") # Default to custom as we don't save provider state yet
        self.entry_url.insert(0, s.get("ollama_url", AppConfig.OLLAMA_URL))
        self.entry_apikey.insert(0, s.get("api_key", ""))
        
        # Load available models into the combobox
        models = s.get("available_models", [AppConfig.DEFAULT_MODEL])
        self.entry_model.configure(values=models)
        self.entry_model.set(s.get("model", AppConfig.DEFAULT_MODEL))
        
        self.entry_temp.insert(0, str(s.get("temperature", AppConfig.AI_TEMPERATURE)))
        self.entry_ctx.insert(0, str(s.get("ctx_size", AppConfig.AI_CTX_SIZE)))
        self.entry_timeout.insert(0, str(s.get("timeout", AppConfig.TIMEOUT)))
        
        self.option_theme.set(s.get("appearance", "System"))
        self.entry_font_mono.insert(0, s.get("font_mono", AppConfig.FONT_MONO))
        self.entry_font_sans.insert(0, s.get("font_sans", AppConfig.FONT_SANS))
        self.entry_size_query.insert(0, str(s.get("size_query", AppConfig.SIZE_QUERY)))
        self.entry_size_expl.insert(0, str(s.get("size_explanation", AppConfig.SIZE_EXPLANATION)))
        
        # New Formatting Settings
        kw_case = s.get("sql_keyword_case", AppConfig.SQL_KEYWORD_CASE)
        if kw_case == "upper": self.option_keyword_case.set("UPPER")
        elif kw_case == "lower": self.option_keyword_case.set("lower")
        else: self.option_keyword_case.set("Capitalize")
        
        self.option_indent_width.set(f"{s.get('sql_indent_width', AppConfig.SQL_INDENT_WIDTH)} Spaces")
        if s.get("sql_comma_first", AppConfig.SQL_COMMA_FIRST):
            self.switch_comma_first.select()
        if s.get("sql_compact_select", AppConfig.SQL_COMPACT_SELECT):
            self.switch_compact_select.select()

        self.text_prompt_chat.insert("1.0", s.get("system_prompt_chat", AppConfig.DEFAULT_SYSTEM_PROMPT_CHAT))

    def reset_chat_prompt(self):
        self.text_prompt_chat.delete("1.0", tk.END)
        self.text_prompt_chat.insert("1.0", AppConfig.DEFAULT_SYSTEM_PROMPT_CHAT)

    def save_settings(self):
        try:
            new_settings = self.parent.settings.copy()
            
            # Update values
            new_settings["ollama_url"] = self.entry_url.get().strip()
            new_settings["api_key"] = self.entry_apikey.get().strip()
            new_settings["model"] = self.entry_model.get().strip()
            new_settings["temperature"] = float(self.entry_temp.get())
            new_settings["ctx_size"] = int(self.entry_ctx.get())
            new_settings["timeout"] = int(self.entry_timeout.get())
            
            new_settings["appearance"] = self.option_theme.get()
            new_settings["font_mono"] = self.entry_font_mono.get().strip()
            new_settings["font_sans"] = self.entry_font_sans.get().strip()
            new_settings["size_query"] = int(self.entry_size_query.get())
            new_settings["size_explanation"] = int(self.entry_size_expl.get())
            
            # New Formatting Settings
            new_settings["sql_keyword_case"] = self.option_keyword_case.get().lower()
            new_settings["sql_indent_width"] = int(self.option_indent_width.get().split()[0])
            new_settings["sql_comma_first"] = self.switch_comma_first.get() == 1
            new_settings["sql_compact_select"] = self.switch_compact_select.get() == 1

            new_settings["system_prompt_chat"] = self.text_prompt_chat.get("1.0", tk.END).strip()
            # Save the current list of values from the combobox
            new_settings["available_models"] = self.entry_model.cget("values")
            
            # Apply to parent
            self.parent.apply_settings(new_settings)
            self.destroy()
            
        except ValueError as e:
            tk.messagebox.showerror("Invalid Input", f"Please check your inputs (numbers vs text).\nError: {e}")

class HelpDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("QueryTune Help & Usage")
        self.geometry("600x650")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Text Area with unified background
        box_bg_color = ("#FFFFFF", "#2B2B2B") # White in light mode, Dark Gray in dark mode
        
        self.text_frame = ctk.CTkFrame(self, fg_color=box_bg_color, border_width=1)
        self.text_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        help_text = (
            "QUICK START GUIDE\n"
            "-----------------\n"
            "1. Start Ollama: Ensure Ollama is running (`ollama serve`).\n"
            "2. Select Model: Enter the model name (e.g., qwen2.5-coder:7b).\n"
            "3. Database: Select the target SQL dialect for better optimization.\n\n"
            
            "ANALYSIS MODES\n"
            "--------------\n"
            "• OPTIMIZE: Best for refactoring. Generates structured JSON output with "
            "the optimized query, required indices, and a technical explanation.\n"
            "• CHAT MODE: Best for exploration. Provides a natural language "
            "analysis of the query in real-time (streaming).\n\n"
            
            "ADVANCED FEATURES\n"
            "-----------------\n"
            "• CONTEXT BOX: Use this to provide the AI with extra info like:\n"
            "  - Table sizes (e.g., 'Table ACME has 1M rows')\n"
            "  - Constraints (e.g., 'Do not use JOINs')\n"
            "  - Existing Indices or Schema details.\n"
            "• PREFERENCES: Access via CMD+, (macOS) to change UI fonts, "
            "Ollama URL, Temperature, and Timeout settings.\n\n"
            
            "DISTRIBUTION NOTE\n"
            "-----------------\n"
            "If sharing this app, users may need to Right-Click -> Open the first time "
            "to bypass macOS security warnings for unsigned developers.\n\n"
            
            "GITHUB & UPDATES\n"
            "----------------\n"
            "Report bugs or contribute at:"
        )

        self.textbox = ctk.CTkTextbox(self.text_frame, 
                                      font=(AppConfig.FONT_SANS, 13), 
                                      wrap="word",
                                      fg_color="transparent",
                                      scrollbar_button_color=("#C0C0C0", "#505050"))
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.textbox.insert("1.0", help_text)
        self.textbox.configure(state="disabled")

        # GitHub Link inside the same white/dark box
        self.link_label = ctk.CTkLabel(self.text_frame, text="https://github.com/meob/QueryTune", 
                                      text_color="#3498DB", cursor="hand2",
                                      fg_color="transparent",
                                      font=ctk.CTkFont(size=13, underline=True),
                                      anchor="w")
        self.link_label.pack(fill="x", padx=15, pady=(0, 15))
        self.link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/meob/QueryTune"))

        self.btn_close = ctk.CTkButton(self, text="Close", command=self.destroy)
        self.btn_close.grid(row=1, column=0, pady=(0, 20))

class QueryTuneApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Default Settings
        self.settings = {
            "db_type": AppConfig.DB_OPTIONS[0],
            "model": AppConfig.DEFAULT_MODEL,
            "appearance": "System",
            "ollama_url": AppConfig.OLLAMA_URL,
            "timeout": AppConfig.TIMEOUT,
            "temperature": AppConfig.AI_TEMPERATURE,
            "ctx_size": AppConfig.AI_CTX_SIZE,
            "font_mono": AppConfig.FONT_MONO,
            "font_sans": AppConfig.FONT_SANS,
            "size_query": AppConfig.SIZE_QUERY,
            "size_indices": AppConfig.SIZE_INDICES,
            "size_explanation": AppConfig.SIZE_EXPLANATION,
            "system_prompt_chat": AppConfig.DEFAULT_SYSTEM_PROMPT_CHAT,
            "available_models": [AppConfig.DEFAULT_MODEL]
        }

        self.current_optimization_id = 0
        self.is_optimizing = False

        self.title(f"{AppConfig.APP_NAME} - AI SQL Optimizer")
        self.geometry("800x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_menu()
        self._init_sidebar()
        self._init_main_area()
        
        self.load_settings()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # On macOS, we can hook into the Application Menu (the one named QueryTune)
        if platform.system() == "Darwin":
            self.createcommand('tkAboutDialog', self.show_about)
            self.createcommand('::tk::mac::ShowPreferences', self.open_settings)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Usage Guide", command=self.show_help)
        
        # If not on macOS, add About and Preferences to menus
        if platform.system() != "Darwin":
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="Preferences", command=self.open_settings)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.on_closing)
            
            help_menu.add_separator()
            help_menu.add_command(label="About QueryTune", command=self.show_about)

    def open_settings(self, *args):
        SettingsDialog(self)

    def show_about(self):
        messagebox.showinfo(
            "About QueryTune",
            f"{AppConfig.APP_NAME}\nVersion {AppConfig.VERSION}\n\n"
            "An AI-powered SQL optimizer using local LLMs.\n"
            "Powered by Ollama & CustomTkinter."
        )

    def show_help(self):
        HelpDialog(self)
    
    def _init_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        try:
            image_path = resource_path(os.path.join("assets", "icon.png"))
            self.logo_image = ctk.CTkImage(Image.open(image_path), size=(80, 80))
            self.logo_image_label = ctk.CTkLabel(self.sidebar_frame, text="", image=self.logo_image)
            self.logo_image_label.grid(row=0, column=0, padx=20, pady=(30, 0))
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text=AppConfig.APP_NAME, font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=1, column=0, padx=20, pady=(5, 20))

        self.db_label = ctk.CTkLabel(self.sidebar_frame, text="Database Type:", anchor="w")
        self.db_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        self.db_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=AppConfig.DB_OPTIONS)
        self.db_optionemenu.grid(row=3, column=0, padx=20, pady=10)

        self.model_label = ctk.CTkLabel(self.sidebar_frame, text="Model:", anchor="w")
        self.model_label.grid(row=4, column=0, padx=20, pady=(10, 0))
        self.model_entry = ctk.CTkComboBox(self.sidebar_frame, values=[AppConfig.DEFAULT_MODEL])
        self.model_entry.set(AppConfig.DEFAULT_MODEL)
        self.model_entry.grid(row=5, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.set("System")
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

    def _init_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        # Row layout: 0=Labels, 1=Input, 2=Context, 3=Buttons, 4=Tabs, 5=Progress
        self.main_frame.grid_rowconfigure(1, weight=1) 
        self.main_frame.grid_rowconfigure(4, weight=3)

        # Header Frame for Label + Context Switch
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.input_label = ctk.CTkLabel(self.header_frame, text="Paste your SQL Query here:", font=ctk.CTkFont(weight="bold"))
        self.input_label.pack(side="left")
        
        self.context_switch = ctk.CTkSwitch(self.header_frame, text="Show Context window", command=self.toggle_context)
        self.context_switch.pack(side="right")

        self.format_button = ctk.CTkButton(self.header_frame, text="Format SQL", 
                                           command=self.format_input_query,
                                           width=80, height=24, font=ctk.CTkFont(size=12))
        self.format_button.pack(side="right", padx=10)

        # Input Query
        self.input_text = ctk.CTkTextbox(self.main_frame, undo=True, font=(AppConfig.FONT_MONO, AppConfig.SIZE_QUERY))
        self.input_text.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # Context Frame (Initially hidden)
        self.context_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        # Don't grid it yet, toggle_context handles it
        
        self.context_label = ctk.CTkLabel(self.context_frame, text="Additional Context (Table sizes, constraints, specific instructions):", anchor="w")
        self.context_label.pack(fill="x", pady=(5,0))
        self.context_text = ctk.CTkTextbox(self.context_frame, height=80, font=(AppConfig.FONT_SANS, 12))
        self.context_text.pack(fill="x", pady=5)

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        self.button_frame.grid(row=3, column=0, pady=10, sticky="ew")
        
        # Center Buttons Container
        self.center_btn_frame = ctk.CTkFrame(self.button_frame, fg_color="transparent")
        self.center_btn_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.optimize_button = ctk.CTkButton(self.center_btn_frame, text="Optimize", 
                                             command=lambda: self.start_optimization_thread("optimize"), 
                                             width=140, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        self.optimize_button.pack(side="left", padx=10)

        self.explain_button = ctk.CTkButton(self.center_btn_frame, text="Chat mode", 
                                            command=lambda: self.start_optimization_thread("explain"),
                                            fg_color="#2980B9", hover_color="#3498DB",
                                            width=140, height=40, font=ctk.CTkFont(size=14, weight="bold"))
        self.explain_button.pack(side="left", padx=10)

        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop", command=self.stop_optimization, 
                                         fg_color="#C0392B", hover_color="#E74C3C", width=80, state="disabled")
        self.stop_button.pack(side="right", padx=0)

        # Output Tabs
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=4, column=0, sticky="nsew")
        self.tabview.add("Optimized Query")
        self.tabview.add("Index Suggestions")
        self.tabview.add("Analysis")

        self.output_query = ctk.CTkTextbox(self.tabview.tab("Optimized Query"), font=(AppConfig.FONT_MONO, AppConfig.SIZE_QUERY))
        self.output_query.pack(fill="both", expand=True, padx=5, pady=5)
        self.copy_query_btn = ctk.CTkButton(self.tabview.tab("Optimized Query"), text="Copy Query", 
                                            command=lambda: self.copy_to_clipboard(self.output_query.get("1.0", tk.END)))
        self.copy_query_btn.pack(pady=5)
        
        self.output_indices = ctk.CTkTextbox(self.tabview.tab("Index Suggestions"), font=(AppConfig.FONT_MONO, AppConfig.SIZE_INDICES))
        self.output_indices.pack(fill="both", expand=True, padx=5, pady=5)
        self.copy_indices_btn = ctk.CTkButton(self.tabview.tab("Index Suggestions"), text="Copy Indices", 
                                              command=lambda: self.copy_to_clipboard(self.output_indices.get("1.0", tk.END)))
        self.copy_indices_btn.pack(pady=5)

        self.output_explanation = ctk.CTkTextbox(self.tabview.tab("Analysis"), font=(AppConfig.FONT_SANS, AppConfig.SIZE_EXPLANATION), wrap="word")
        self.output_explanation.pack(fill="both", expand=True, padx=5, pady=5)
        self.copy_expl_btn = ctk.CTkButton(self.tabview.tab("Analysis"), text="Copy Analysis", 
                                           command=lambda: self.copy_to_clipboard(self.output_explanation.get("1.0", tk.END)))
        self.copy_expl_btn.pack(pady=5)

        self.progressbar = ctk.CTkProgressBar(self.main_frame)
        self.progressbar.grid(row=5, column=0, sticky="ew", pady=10)
        self.progressbar.set(0)
        self.progressbar.grid_remove()

    def toggle_context(self):
        if self.context_switch.get() == 1:
            self.context_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
            self.main_frame.grid_rowconfigure(1, weight=1) # Input shrinks slightly
        else:
            self.context_frame.grid_forget()
            self.main_frame.grid_rowconfigure(1, weight=2) # Input grows back

    def align_sql_keywords(self, sql):
        """Advanced post-processing for soft right-alignment using nesting levels"""
        import re
        s = self.settings
        indent_width = s.get("sql_indent_width", 2)
        compact_select = s.get("sql_compact_select", False)

        # Offsets to achieve end-alignment at column 6 (length of SELECT)
        # adjusted based on indent_width if needed, but usually 
        # relative to the SELECT anchor.
        offsets = {
            'FROM': 2, 'JOIN': 2, 'LEFT': 2, 'RIGHT': 2, 'INNER': 2,
            'WHERE': 1, 'AND': 3, 'OR': 4, 'ON': 4,
            'GROUP': 1, 'ORDER': 1, 'HAVING': 1, 'LIMIT': 1,
            'SET': 3, 'VALUES': 0, 'INSERT': 0, 'UPDATE': 0, 'DELETE': 0
        }
        
        lines = sql.split('\n')
        
        # Compact SELECT logic: if enabled, try to join lines between SELECT and next keyword
        if compact_select:
            new_lines = []
            buf = []
            in_select = False
            for line in lines:
                up = line.strip().upper()
                if up.startswith('SELECT'):
                    in_select = True
                    buf.append(line.strip())
                elif in_select and any(up.startswith(k) for k in offsets):
                    new_lines.append(" ".join(buf))
                    buf = [line]
                    in_select = False
                elif in_select:
                    buf.append(line.strip())
                else:
                    new_lines.append(line)
            if buf:
                new_lines.append(" ".join(buf) if in_select else buf[0])
            lines = new_lines

        aligned_lines = []
        nesting_level = 0
        
        for line in lines:
            stripped = line.lstrip()
            if not stripped:
                aligned_lines.append("")
                continue
                
            # Detect subquery start/end
            is_subquery_start = stripped.startswith('(') and 'SELECT' in stripped.upper()
            
            # If the line starts with a closing paren, we are exiting a level
            if stripped.startswith(')'):
                nesting_level = max(0, nesting_level - 1)
            
            # Base indentation
            current_base = nesting_level * (indent_width + 1)
            
            # Get the first word (handling the starting '(' for subqueries)
            first_word = stripped.split()[0].upper().replace('(', '')
            
            if is_subquery_start:
                new_indent = (nesting_level * (indent_width + 1)) + indent_width
                new_line = (" " * new_indent) + stripped
                if ')' not in stripped:
                    nesting_level += 1
            elif first_word in offsets:
                new_indent = current_base + offsets[first_word]
                new_line = (" " * new_indent) + stripped
            elif first_word == 'SELECT':
                new_line = (" " * current_base) + stripped
            else:
                # Continuation line
                new_indent = current_base + 7
                new_line = (" " * new_indent) + stripped
            
            if ')' in stripped and not stripped.startswith(')'):
                nesting_level = max(0, nesting_level - stripped.count(')'))
                
            aligned_lines.append(new_line)
            
        return '\n'.join(aligned_lines)

    def format_input_query(self):
        query = self.input_text.get("1.0", tk.END).strip()
        if query:
            try:
                s = self.settings
                formatted_sql = sqlparse.format(
                    query, 
                    reindent=True, 
                    keyword_case=s.get("sql_keyword_case", "upper"),
                    indent_width=s.get("sql_indent_width", 2),
                    comma_first=s.get("sql_comma_first", False)
                )
                formatted_sql = self.align_sql_keywords(formatted_sql)
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", formatted_sql)
            except Exception as e:
                print(f"Format error: {e}")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def load_settings(self):
        try:
            if os.path.exists(AppConfig.SETTINGS_FILE):
                with open(AppConfig.SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
            self.apply_settings()
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def save_settings(self):
        # Capture current sidebar state into settings before saving
        self.settings["db_type"] = self.db_optionemenu.get()
        self.settings["model"] = self.model_entry.get().strip()
        self.settings["appearance"] = self.appearance_mode_optionemenu.get()
        
        try:
            with open(AppConfig.SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def apply_settings(self, new_settings=None):
        if new_settings:
            self.settings.update(new_settings)
            
        s = self.settings
        
        # Update Sidebar
        self.db_optionemenu.set(s.get("db_type", AppConfig.DB_OPTIONS[0]))
        
        # Update Model List and Current Value
        models = s.get("available_models", [AppConfig.DEFAULT_MODEL])
        self.model_entry.configure(values=models)
        self.model_entry.set(s.get("model", AppConfig.DEFAULT_MODEL))
        
        mode = s.get("appearance", "System")
        self.appearance_mode_optionemenu.set(mode)
        ctk.set_appearance_mode(mode)
        
        # Update Fonts
        font_mono = (s.get("font_mono", AppConfig.FONT_MONO), int(s.get("size_query", AppConfig.SIZE_QUERY)))
        font_expl = (s.get("font_sans", AppConfig.FONT_SANS), int(s.get("size_explanation", AppConfig.SIZE_EXPLANATION)))
        font_indices = (s.get("font_mono", AppConfig.FONT_MONO), int(s.get("size_indices", AppConfig.SIZE_INDICES)))
        
        self.input_text.configure(font=font_mono)
        self.output_query.configure(font=font_mono)
        self.output_indices.configure(font=font_indices)
        self.output_explanation.configure(font=font_expl)

    def on_closing(self):
        self.save_settings()
        self.destroy()

    def start_optimization_thread(self, mode="optimize"):
        query = self.input_text.get("1.0", tk.END).strip()
        context = self.context_text.get("1.0", tk.END).strip()
        
        if not query:
            return

        self.optimize_button.configure(state="disabled")
        self.explain_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progressbar.grid()
        self.progressbar.configure(mode="indeterminate")
        self.progressbar.start()
        
        # Clear previous outputs
        self.output_query.delete("1.0", tk.END)
        self.output_indices.delete("1.0", tk.END)
        self.output_explanation.delete("1.0", tk.END)

        if mode == "optimize":
            self.output_query.insert("1.0", "Optimizing query... please wait.")
            self.output_indices.insert("1.0", "Analyzing schema...")
            self.output_explanation.insert("1.0", "Thinking...")
            self.tabview.set("Optimized Query")
        else:
            self.output_explanation.insert("1.0", "Chatting with DBA... \n\n")
            self.tabview.set("Analysis")

        self.current_optimization_id += 1
        self.is_optimizing = True
        
        req_id = self.current_optimization_id
        threading.Thread(target=self.run_optimization, args=(query, context, req_id, mode), daemon=True).start()

    def stop_optimization(self):
        if self.is_optimizing:
            self.is_optimizing = False
            self.current_optimization_id += 1
            self.finalize_task()
            self.output_query.delete("1.0", tk.END)
            self.output_query.insert("1.0", "Optimization stopped by user.")
            self.output_indices.delete("1.0", tk.END)
            self.output_explanation.delete("1.0", tk.END)

    def run_optimization(self, query, context, req_id, mode):
        db_type = self.db_optionemenu.get()
        model = self.model_entry.get() or self.settings.get("model", AppConfig.DEFAULT_MODEL)
        url = self.settings.get("ollama_url", AppConfig.OLLAMA_URL)
        api_key = self.settings.get("api_key", "")
        temperature = float(self.settings.get("temperature", AppConfig.AI_TEMPERATURE))
        ctx_size = int(self.settings.get("ctx_size", AppConfig.AI_CTX_SIZE))
        timeout = int(self.settings.get("timeout", AppConfig.TIMEOUT))

        # Build Headers
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Build Prompt based on mode
        if mode == "optimize":
            system_prompt = f"You are an expert {db_type} DBA. Optimize the query and return a valid JSON."
            user_content = f"""Input Query: {query}\nContext: {context}\n\nReturn a JSON object with exactly these keys:
- "optimized_query": the optimized SQL string.
- "indices": a string containing one or more SQL CREATE INDEX statements (or an empty string if none needed).
- "explanation": a string with your reasoning."""
            format_type = {"type": "json_object"} if "openai" in url.lower() else "json"
            stream = False
        else:
            system_prompt_template = self.settings.get("system_prompt_chat", AppConfig.DEFAULT_SYSTEM_PROMPT_CHAT)
            system_prompt = system_prompt_template.replace("{db_type}", db_type)
            user_content = f"Input Query: {query}\nContext: {context}"
            format_type = ""
            stream = True

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": ctx_size
        }
        
        # Some providers use "format", some "response_format"
        if mode == "optimize":
            if "openai" in url.lower():
                payload["response_format"] = {"type": "json_object"}
            else:
                payload["format"] = "json"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
                stream=stream 
            )
            response.raise_for_status()

            if mode == "explain" and stream:
                for line in response.iter_lines():
                    if req_id != self.current_optimization_id or not self.is_optimizing:
                        break
                    if line:
                        try:
                            # Standard OpenAI/Ollama v1 format
                            raw_line = line.decode('utf-8').replace('data: ', '').strip()
                            if raw_line == "[DONE]": break
                            json_chunk = json.loads(raw_line)
                            
                            # Content is in choices[0].delta.content for stream
                            token = ""
                            if "choices" in json_chunk:
                                token = json_chunk["choices"][0].get("delta", {}).get("content", "")
                            elif "message" in json_chunk: # Some Ollama versions
                                token = json_chunk["message"].get("content", "")
                            elif "response" in json_chunk: # Old Ollama fallback
                                token = json_chunk.get("response", "")
                                
                            if token:
                                self.after(0, lambda t=token: self.stream_token(t, req_id))
                        except:
                            pass
                self.after(0, self.finalize_task)
            
            else:
                if req_id != self.current_optimization_id or not self.is_optimizing:
                    return

                result_json = response.json()
                
                # Parse standard OpenAI/Ollama v1 response
                if "choices" in result_json:
                    raw_content = result_json["choices"][0]["message"]["content"]
                else:
                    raw_content = result_json.get("response", "{}")
                
                try:
                    content = json.loads(raw_content)
                except json.JSONDecodeError:
                    import re
                    json_match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
                    if json_match:
                        content = json.loads(json_match.group(1))
                    else:
                        raise ValueError("Could not parse AI response as JSON")
                
                self.after(0, lambda: self.update_ui(content, req_id))

        except Exception as e:
            if req_id == self.current_optimization_id and self.is_optimizing:
                error_msg = str(e)
                self.after(0, lambda: self.show_error(error_msg))

    def stream_token(self, token, req_id):
        if req_id != self.current_optimization_id:
            return
        self.output_explanation.insert(tk.END, token)
        self.output_explanation.see(tk.END)

    def update_ui(self, content, req_id):
        if req_id != self.current_optimization_id:
            return

        self.output_query.delete("1.0", tk.END)
        self.output_indices.delete("1.0", tk.END)
        self.output_explanation.delete("1.0", tk.END)

        # 1. Optimized Query
        raw_sql = content.get("optimized_query", "")
        try:
            formatted_sql = sqlparse.format(raw_sql, reindent=True, keyword_case='upper')
            formatted_sql = self.align_sql_keywords(formatted_sql)
        except Exception:
            formatted_sql = raw_sql
        self.output_query.insert("1.0", formatted_sql if formatted_sql else "No query returned")

        # 2. Index Suggestions (Handle both string and structured JSON)
        raw_indices = content.get("indices", "")
        sql_indices = ""

        def dict_to_sql(d):
            table = d.get('table', 'table_name')
            idx_name = d.get('index_name', f"idx_{table}_{''.join(filter(str.isalnum, str(d.get('columns',[''])[0])))[:10]}")
            cols = d.get('columns', [])
            if isinstance(cols, list):
                cols_str = ", ".join(cols)
            else:
                cols_str = str(cols)
            return f"CREATE INDEX {idx_name} ON {table} ({cols_str});"

        if isinstance(raw_indices, list):
            statements = []
            for item in raw_indices:
                if isinstance(item, dict):
                    statements.append(dict_to_sql(item))
                else:
                    statements.append(str(item))
            sql_indices = "\n".join(statements)
        elif isinstance(raw_indices, dict):
            sql_indices = dict_to_sql(raw_indices)
        else:
            sql_indices = str(raw_indices)

        # Final Cleanup: remove empty lines and isolated ";"
        clean_lines = [line.strip() for line in sql_indices.split('\n') if line.strip() and line.strip() != ';']
        sql_indices = "\n".join(clean_lines)

        try:
            formatted_indices = sqlparse.format(sql_indices, reindent=True, keyword_case='upper')
        except Exception:
            formatted_indices = sql_indices

        self.output_indices.insert("1.0", formatted_indices if formatted_indices else "None")
        
        # 3. Explanation
        self.output_explanation.insert("1.0", content.get("explanation", "No explanation provided"))
        self.finalize_task()

    def show_error(self, error_msg):
        self.output_explanation.delete("1.0", tk.END)
        self.output_explanation.insert("1.0", f"Error: {error_msg}\n\nCheck Ollama connection or Model name.")
        self.finalize_task()

    def finalize_task(self):
        self.is_optimizing = False
        self.progressbar.stop()
        self.progressbar.grid_remove()
        self.optimize_button.configure(state="normal")
        self.explain_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text.strip())

if __name__ == "__main__":
    app = QueryTuneApp()
    app.mainloop()
