import os
import json
import requests
import time
from typing import Dict, Any

from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from aqt.webview import AnkiWebView

# Import các module con
from .debug_tools import DebugTools
from .chat_window import ChatWindow
from .config_dialogs import ConfigDialog, DeckConfigDialog
from .languages import get_text


class GeminiChatBot:
    def __init__(self):
        self.debug = DebugTools("GeminiChatBot")
        # self.debug.log("Initializing GeminiChatBot...")

        self.config = self.load_config()
        self.current_card = None
        self.has_chatted_for_card = False
        self.chat_window: ChatWindow = None # Type hint for better clarity

        self.setup_menu()
        self.register_handlers()
        self.register_hooks()
        self.register_shortcut()

        # self.debug.log("GeminiChatBot initialized successfully", True)

    def register_shortcut(self):
        """Register global shortcut Ctrl+Y to open chat window"""
        try:
            # Ctrl + Y → open ChatBot
            shortcut_open = QShortcut(QKeySequence("Ctrl+Y"), mw)
            shortcut_open.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut_open.activated.connect(self.open_chat_window)

            # Ctrl + U → close ChatBot
            shortcut_close = QShortcut(QKeySequence("Ctrl+U"), mw)
            shortcut_close.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut_close.activated.connect(self.close_chat_window)

            # self.debug.log("Shortcut Ctrl+Y and Ctrl + U registered for Gemini ChatBot")
        except Exception as e:
            # self.debug.log(f"Error registering shortcut: {e}", True)
            pass

    def register_handlers(self):
        """Register message handlers"""
        from aqt.gui_hooks import webview_did_receive_js_message
        webview_did_receive_js_message.append(self.handle_pycmd)
        # self.debug.log("PyCmd handlers registered")

    def register_hooks(self):
        """Register all hooks"""
        from aqt import gui_hooks

        hooks = [
            (gui_hooks.reviewer_did_show_question, self.on_show_question),
            (gui_hooks.reviewer_will_end, self.on_review_end),
            (gui_hooks.profile_will_close, self.cleanup),
            (gui_hooks.state_will_change, self.on_state_change)
        ]

        for hook, handler in hooks:
            hook.append(handler)

        # self.debug.log(f"Registered {len(hooks)} hooks")

    def on_state_change(self, new_state, old_state):
        """Debug state changes"""
        # self.debug.log(f"State change: {old_state} → {new_state}")
        if old_state == "review" and new_state != "review":
            # self.debug.log("Leaving review → cleaning UI")
            self._cleanup_injected_elements()

            if self.chat_window:
                self.chat_window.close()
                self.chat_window = None

    def handle_pycmd(self, handled, cmd, context):
        """
        Handle pycmd messages
        """
        already_handled, result = handled

        if already_handled:
            return handled

        # self.debug.log(f"PyCmd received: {cmd}")

        if cmd == "gemini_chat_open":
            self.open_chat_window()
            return (True, None)
        elif cmd.startswith("gemini_chat_send:"):
            message = cmd.split(":", 1)[1]
            if self.chat_window:
                self.chat_window.send_message(message)
                self.has_chatted_for_card = True
            return (True, None)
        
        return handled

    def load_config(self) -> Dict[str, Any]:
        """Load configuration với defaults"""
        default_config = {
            "enabled": True,
            "api_key": "",
            "max_tokens": 500,
            "selected_prompt": "explain_simple",
            "target_field": "Front",
            "custom_prompts": {
                "explain_simple": "Bạn có muốn biết thêm về: {text} ngắn gọn trong 100 chữ",
                "synonyms_antonyms": "Từ đồng nghĩa/trái nghĩa của: {text}",
                "real_world_examples": "Ví dụ thực tế về: {text}",
                "memory_tips": "Mẹo ghi nhớ cho: {text}"
            },
            "deck_settings": {}
        }

        try:
            user_config = mw.addonManager.getConfig(__name__) or {}
            # self.debug.log(f"User config loaded: {user_config}")
            # Deep merge
            config = default_config.copy()
            config.update(user_config)
            config["custom_prompts"] = {**default_config["custom_prompts"], **user_config.get("custom_prompts", {})}

            # self.debug.log("Configuration loaded successfully")
            return config

        except Exception as e:
            # self.debug.log(f"Config load error: {e}", True)
            return default_config

    def save_config(self):
        """Save configuration"""
        try:
            mw.addonManager.writeConfig(__name__, self.config)
            # self.debug.log("Configuration saved")
        except Exception as e:
            # self.debug.log(f"Config save error: {e}", True)
            pass

    def setup_menu(self):
        """Add menu items"""
        try:
            menu = QMenu("Gemini ChatBot", mw)
            lang = self.config.get("language", "vi")

            actions = [
                (get_text(lang, "menu_config"), self.show_config_dialog),
                (get_text(lang, "menu_deck_config"), self.show_deck_config),
                (get_text(lang, "menu_test_api"), self.test_api_key),
                (get_text(lang, "menu_debug"), self.show_debug_info)
            ]

            for name, handler in actions:
                action = QAction(name, mw)
                action.triggered.connect(handler)
                menu.addAction(action)

            mw.form.menuTools.addMenu(menu)
            # self.debug.log("Menu setup completed")

        except Exception as e:
            # self.debug.log(f"Menu setup error: {e}", True)
            pass

    def show_debug_info(self):
        """Show debug information"""
        info = [
            "=== GEMINI CHATBOT DEBUG INFO ===",
            f"Addon Enabled: {self.config['enabled']}",
            f"API Key Set: {'Yes' if self.config['api_key'] else 'No'}",
            f"Current Card: {self.current_card.id if self.current_card else 'None'}",
            f"Reviewer Active: {mw.reviewer is not None}",
            f"WebView Ready: {mw.reviewer and mw.reviewer.web is not None}",
            "",
            "Debug URL: http://localhost:8080",
            "Check console for detailed logs"
        ]

        showInfo("\n".join(info))

    def on_show_question(self, card):
        """Called when question is shown"""
        try:
            # self.debug.log("=== on_show_question TRIGGERED ===")
            # self.debug.log(self.debug.inspect_card(card))

            # Remove existing chat UI and button on new card
            self._cleanup_injected_elements()

            # Check if addon is enabled
            if not self.config["enabled"]:
                # self.debug.log("Addon disabled in config")
                return

            # Check if reviewer and webview are ready
            if not mw.reviewer or not mw.reviewer.web:
                # self.debug.log("Reviewer or WebView not ready")
                return

            self.current_card = card
            self.has_chatted_for_card = False

            # Get deck settings
            deck_id = str(card.did)
            deck_settings = self.config["deck_settings"].get(deck_id, {})
            deck_enabled = deck_settings.get("enabled", False)

            if not deck_enabled:
                # self.debug.log(f"ChatBot disabled for deck {deck_id}")
                return

            # Get target field text
            target_field = deck_settings.get("target_field", self.config["target_field"])
            field_text = self.get_field_text(card, target_field)

            if not field_text.strip():
                # self.debug.log(f"Empty field text for field: {target_field}")
                return

            # Get prompt template
            prompt_key = deck_settings.get("selected_prompt", self.config["selected_prompt"])
            prompt_template = self.config["custom_prompts"].get(prompt_key, "Bạn có muốn biết thêm về: {text}")

            # self.debug.log(f"Showing button for: {field_text[:30]}...")
            self.show_chatbot_button(field_text, prompt_template)
            shortcut_open.activated.connect(self.open_chat_window)

            # Ctrl + U → close ChatBot
            shortcut_close = QShortcut(QKeySequence("Ctrl+U"), mw)
            shortcut_close.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut_close.activated.connect(self.close_chat_window)

            # self.debug.log("Shortcut Ctrl+Y and Ctrl + U registered for Gemini ChatBot")
        except Exception as e:
            # self.debug.log(f"Error registering shortcut: {e}", True)
            pass

    def register_handlers(self):
        """Register message handlers"""
        from aqt.gui_hooks import webview_did_receive_js_message
        webview_did_receive_js_message.append(self.handle_pycmd)
        # self.debug.log("PyCmd handlers registered")

    def register_hooks(self):
        """Register all hooks"""
        from aqt import gui_hooks

        hooks = [
            (gui_hooks.reviewer_did_show_question, self.on_show_question),
            (gui_hooks.reviewer_will_end, self.on_review_end),
            (gui_hooks.profile_will_close, self.cleanup),
            (gui_hooks.state_will_change, self.on_state_change)
        ]

        for hook, handler in hooks:
            hook.append(handler)

        # self.debug.log(f"Registered {len(hooks)} hooks")

    def on_state_change(self, new_state, old_state):
        """Debug state changes"""
        # self.debug.log(f"State change: {old_state} → {new_state}")
        if old_state == "review" and new_state != "review":
            # self.debug.log("Leaving review → cleaning UI")
            self._cleanup_injected_elements()

            if self.chat_window:
                self.chat_window.close()
                self.chat_window = None

    def handle_pycmd(self, handled, cmd, context):
        """
        Handle pycmd messages
        """
        already_handled, result = handled

        if already_handled:
            return handled

        # self.debug.log(f"PyCmd received: {cmd}")

        if cmd == "gemini_chat_open":
            self.open_chat_window()
            return (True, None)
        elif cmd.startswith("gemini_chat_send:"):
            message = cmd.split(":", 1)[1]
            if self.chat_window:
                self.chat_window.send_message(message)
                self.has_chatted_for_card = True
            return (True, None)
        
        return handled

    def load_config(self) -> Dict[str, Any]:
        """Load configuration với defaults"""
        default_config = {
            "enabled": True,
            "api_key": "",
            "max_tokens": 500,
            "selected_prompt": "explain_simple",
            "target_field": "Front",
            "custom_prompts": {
                "explain_simple": "Bạn có muốn biết thêm về: {text} ngắn gọn trong 100 chữ",
                "synonyms_antonyms": "Từ đồng nghĩa/trái nghĩa của: {text}",
                "real_world_examples": "Ví dụ thực tế về: {text}",
                "memory_tips": "Mẹo ghi nhớ cho: {text}"
            },
            "deck_settings": {}
        }

        try:
            user_config = mw.addonManager.getConfig(__name__) or {}
            # self.debug.log(f"User config loaded: {user_config}")
            # Deep merge
            config = default_config.copy()
            config.update(user_config)
            config["custom_prompts"] = {**default_config["custom_prompts"], **user_config.get("custom_prompts", {})}

            # self.debug.log("Configuration loaded successfully")
            return config

        except Exception as e:
            # self.debug.log(f"Config load error: {e}", True)
            return default_config

    def save_config(self):
        """Save configuration"""
        try:
            mw.addonManager.writeConfig(__name__, self.config)
            # self.debug.log("Configuration saved")
        except Exception as e:
            # self.debug.log(f"Config save error: {e}", True)
            pass

    def setup_menu(self):
        """Add menu items"""
        try:
            menu = QMenu("Gemini ChatBot", mw)
            lang = self.config.get("language", "vi")

            actions = [
                (get_text(lang, "menu_config"), self.show_config_dialog),
                (get_text(lang, "menu_deck_config"), self.show_deck_config),
                (get_text(lang, "menu_test_api"), self.test_api_key),
                (get_text(lang, "menu_debug"), self.show_debug_info)
            ]

            for name, handler in actions:
                action = QAction(name, mw)
                action.triggered.connect(handler)
                menu.addAction(action)

            mw.form.menuTools.addMenu(menu)
            # self.debug.log("Menu setup completed")

        except Exception as e:
            # self.debug.log(f"Menu setup error: {e}", True)
            pass

    def show_debug_info(self):
        """Show debug information"""
        info = [
            "=== GEMINI CHATBOT DEBUG INFO ===",
            f"Addon Enabled: {self.config['enabled']}",
            f"API Key Set: {'Yes' if self.config['api_key'] else 'No'}",
            f"Current Card: {self.current_card.id if self.current_card else 'None'}",
            f"Reviewer Active: {mw.reviewer is not None}",
            f"WebView Ready: {mw.reviewer and mw.reviewer.web is not None}",
            "",
            "Debug URL: http://localhost:8080",
            "Check console for detailed logs"
        ]

        showInfo("\n".join(info))

    def on_show_question(self, card):
        """Called when question is shown"""
        try:
            # self.debug.log("=== on_show_question TRIGGERED ===")
            # self.debug.log(self.debug.inspect_card(card))

            # Remove existing chat UI and button on new card
            self._cleanup_injected_elements()

            # Check if addon is enabled
            if not self.config["enabled"]:
                # self.debug.log("Addon disabled in config")
                return

            # Check if reviewer and webview are ready
            if not mw.reviewer or not mw.reviewer.web:
                # self.debug.log("Reviewer or WebView not ready")
                return

            self.current_card = card
            self.has_chatted_for_card = False

            # Get deck settings
            deck_id = str(card.did)
            deck_settings = self.config["deck_settings"].get(deck_id, {})
            deck_enabled = deck_settings.get("enabled", False)

            if not deck_enabled:
                # self.debug.log(f"ChatBot disabled for deck {deck_id}")
                return

            # Get target field text
            target_field = deck_settings.get("target_field", self.config["target_field"])
            field_text = self.get_field_text(card, target_field)

            if not field_text.strip():
                # self.debug.log(f"Empty field text for field: {target_field}")
                return

            # Get prompt template
            prompt_key = deck_settings.get("selected_prompt", self.config["selected_prompt"])
            prompt_template = self.config["custom_prompts"].get(prompt_key, "Bạn có muốn biết thêm về: {text}")

            # self.debug.log(f"Showing button for: {field_text[:30]}...")
            self.show_chatbot_button(field_text, prompt_template)

        except Exception as e:
            # self.debug.log(f"Error in on_show_question: {e}", True)
            pass

    def get_field_text(self, card, target_field):
        """Get text from target field"""
        note = card.note()

        # Try exact match first
        if target_field in note:
            return note[target_field]

        # Try case-insensitive match
        for field_name, field_value in note.items():
            if field_name.lower() == target_field.lower():
                return field_value

        # Fallback to first field
        if note.fields:
            return note.fields[0]

        return ""

    def show_chatbot_button(self, text: str, prompt: str):
        """Show floating chatbot button"""
        try:
            lang = self.config.get("language", "vi")
            # Format prompt text for tooltip
            display_text = text[:50] + "..." if len(text) > 50 else text
            formatted_prompt = get_text(lang, "tooltip_prompt", text=display_text)

            # CSS với !important để override Anki styles
            css = """
            <style>
            #gemini-chatbot-tooltip-container {
                all: initial !important;
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                z-index: 10000 !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: flex-end !important;
                pointer-events: none !important; /* Let clicks pass through container area */
                font-family: sans-serif !important;
                line-height: normal !important;
            }
            
            #gemini-chatbot-btn {
                all: initial !important;
                position: relative !important; /* Relative to container */
                width: 56px !important;
                height: 56px !important;
                background: linear-gradient(135deg, #4A90E2, #5D5BD9) !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                color: white !important;
                cursor: pointer !important;
                box-shadow: 0 4px 15px rgba(74, 144, 226, 0.4) !important;
                transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                border: none !important;
                outline: none !important;
                pointer-events: auto !important; /* Re-enable pointer events for button */
                margin-top: 10px !important;
                padding: 0 !important;
                box-sizing: border-box !important;
            }
            #gemini-chatbot-btn svg {
                width: 28px !important;
                height: 28px !important;
                fill: white !important;
                transition: transform 0.3s ease !important;
                display: block !important;
                margin: auto !important;
            }
            #gemini-chatbot-btn:hover {
                transform: scale(1.1) translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(74, 144, 226, 0.5) !important;
            }
            #gemini-chatbot-btn:hover svg {
                transform: rotate(15deg) !important;
            }
            #gemini-chatbot-btn:active {
                transform: scale(0.95) !important;
                box-shadow: 0 2px 10px rgba(74, 144, 226, 0.3) !important;
            }
            .gemini-tooltip {
                all: initial !important;
                position: relative !important;
                background: rgba(33, 37, 41, 0.95) !important;
                color: white !important;
                padding: 8px 16px !important;
                border-radius: 8px !important;
                font-size: 14px !important;
                font-family: 'Segoe UI', Roboto, sans-serif !important;
                max-width: 280px !important;
                backdrop-filter: blur(4px) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                opacity: 0 !important;
                visibility: hidden !important;
                transform: translateY(10px) !important;
                transition: all 0.3s ease !important;
                pointer-events: none !important;
                margin-bottom: 10px !important;
                display: block !important;
                line-height: 1.4 !important;
            }
            #gemini-chatbot-tooltip-container:hover .gemini-tooltip {
                opacity: 1 !important;
                visibility: visible !important;
                transform: translateY(0) !important;
            }
            /* Arrow for tooltip */
            .gemini-tooltip::after {
                content: '' !important;
                position: absolute !important;
                bottom: -6px !important;
                right: 24px !important;
                width: 0 !important;
                height: 0 !important;
                border-left: 6px solid transparent !important;
                border-right: 6px solid transparent !important;
                border-top: 6px solid rgba(33, 37, 41, 0.95) !important;
            }
            </style>
            """

            # Robot Icon SVG
            robot_icon = """
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A2.5 2.5 0 0 0 5 15.5A2.5 2.5 0 0 0 7.5 18A2.5 2.5 0 0 0 10 15.5A2.5 2.5 0 0 0 7.5 13m9 0a2.5 2.5 0 0 0-2.5 2.5a2.5 2.5 0 0 0 2.5 2.5a2.5 2.5 0 0 0 2.5-2.5a2.5 2.5 0 0 0-2.5-2.5"/>
            </svg>
            """

            html = f"""
            {css}
            <div id="gemini-chatbot-tooltip-container">
                <div class="gemini-tooltip">{formatted_prompt}</div>
                <button id="gemini-chatbot-btn" onclick="pycmd('gemini_chat_open')">
                    {robot_icon}
                </button>
            </div>
            """

            # Inject into reviewer webview
            js_code = f"""
            console.log('Injecting Gemini ChatBot button...');

            // Remove existing button and tooltip container
            var existingBtnContainer = document.getElementById('gemini-chatbot-tooltip-container');
            if (existingBtnContainer) existingBtnContainer.remove();

            // Add new button
            document.body.insertAdjacentHTML('beforeend', `{html}`);

            console.log('Gemini ChatBot button injected successfully');
            """

            mw.reviewer.web.eval(js_code)
            # self.debug.log("ChatBot button injected successfully")

        except Exception as e:
            # self.debug.log(f"Error showing chatbot button: {e}", True)
            pass

    def _cleanup_injected_elements(self):
        """Remove any previously injected button or chat window from the webview."""
        if mw.reviewer and mw.reviewer.web:
            js_cleanup = """
            var btnContainer = document.getElementById('gemini-chatbot-tooltip-container');
            if (btnContainer) btnContainer.remove();
            var chatContainer = document.getElementById('gemini-chat-container');
            if (chatContainer) chatContainer.remove();
            """
            mw.reviewer.web.eval(js_cleanup)
            # self.debug.log("Cleaned up injected chat UI elements.")

    def on_review_end(self):
        """Clean up when review ends"""
        try:
            self._cleanup_injected_elements()
            # self.debug.log("Review ended - cleanup completed")
        except Exception as e:
            # self.debug.log(f"Cleanup error: {e}")
            pass

    def close_chat_window(self):
        """Close chat window"""
        if self.chat_window:
            self.chat_window.close()
            self.chat_window = None
            # self.debug.log("Chat window closed")    

    def open_chat_window(self):
        """Open chat window"""
        # self.debug.log("Opening chat window...")

        if not self.current_card:
            showInfo(get_text(self.config.get("language", "vi"), "no_active_card"))
            return

        if not self.config["api_key"]:
            showInfo(get_text(self.config.get("language", "vi"), "configure_api_key"))
            return

        try:
            # Initialize chat_window if it doesn't exist
            if self.chat_window is None:
                self.chat_window = ChatWindow(self)
                # Inject/show the chat UI
            self.chat_window.inject_ui()
            # ====== TẠO PROMPT TỰ ĐỘNG ======
            
            deck_id = str(self.current_card.did)
            deck_settings = self.config["deck_settings"].get(deck_id, {})
            # self.debug.log(f"Deck settings for chat window: {deck_settings}")

            target_field = deck_settings.get("target_field")
            # self.debug.log(f"Target field: {target_field}")

            # ✅ Lấy content của field
            card_content = self.get_field_text(self.current_card, target_field)
            # self.debug.log(f"Field value: {card_content}")

            prompt_key = deck_settings.get("selected_prompt") \
                        or self.config.get("selected_prompt")

            # self.debug.log(f"Prompt key selected: {prompt_key}")

            prompt_template = self.config["custom_prompts"].get(prompt_key)

            # Nếu prompt không nằm trong custom_prompt → dùng default
            if not prompt_template:
                prompt_template = "Giải thích về: {text}"

            # self.debug.log(f"Resolved prompt template: {prompt_template}")
            auto_prompt = prompt_template.replace("{text}", card_content)
            # self.debug.log(f"Auto prompt generated: {auto_prompt}")

            if not self.has_chatted_for_card:
                self.chat_window.pre_fill_input(auto_prompt)
            else:
                self.chat_window.pre_fill_input("")
            # self.debug.log("Chat window injected/shown successfully")

        except Exception as e:
            lang = self.config.get("language", "vi")
            if str(e) == "'NoneType' object has no attribute 'lower'":
                showInfo(get_text(lang, "chatbot_disabled_deck"))
            else:
                showInfo(f"Error: {e}")
            # self.debug.log(f"Error opening chat window: {e}", True)

    def call_gemini_api(self, history: str) -> str:
        """Call Gemini API với error handling"""
        lang = self.config.get("language", "vi")
        if not self.config.get("api_key"):
            return get_text(lang, "api_key_missing")

        api_key = self.config.get("api_key")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": history}]}],
            "generationConfig": {
                "maxOutputTokens": self.config.get("max_tokens", 500), 
                "temperature": 0.7,
            }
        }

        # self.debug.log("Calling Gemini API...")

        # retry on 429 (rate limit) with exponential backoff
        max_attempts = 3
        backoff = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(url, json=payload, timeout=30)
                # self.debug.log(f"Response: {response.status_code} - {response.text}")
                if response.status_code == 429:
                    # self.debug.log(f"Gemini API rate-limited (429). Attempt {attempt}/{max_attempts}")
                    if attempt < max_attempts:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    else:
                        return get_text(lang, "rate_limit")
                response.raise_for_status()

                result = response.json()

                # Safely extract response text
                response_text = ""
                try:
                    response_text = result.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
                except (IndexError, TypeError): # Handle cases where candidates or content might be missing
                    # If text is not found, try to return error message from API
                    error_message = result.get("error", {}).get("message", str(result))
                    # self.debug.log(f"Gemini API response parsing error, full result: {result}")
                    return f"❌ Gemini Error: {error_message}"

                # self.debug.log("Gemini API call successful")
                return response_text

            except requests.exceptions.RequestException as e:
                # self.debug.log(f"Gemini API network error (attempt {attempt}): {e}")
                if attempt < max_attempts:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return get_text(lang, "connection_error", e=e)
            except Exception as e:
                # self.debug.log(f"Gemini API unexpected error: {e}", True)
                return get_text(lang, "internal_error", e=e)

    def show_config_dialog(self):
        """Show configuration dialog"""
        try:
            self.config = self.load_config()  # Reload config before showing dialog
            # self.debug.log(f"Current config before dialog: {self.config}")
            dialog = ConfigDialog(self.config, self)
            if dialog.exec():
                self.config = dialog.get_config()
                self.save_config()
                showInfo(get_text(self.config.get("language", "vi"), "config_saved"))
        except Exception as e:
            # self.debug.log(f"Config dialog error: {e}", True)
            pass

    def show_deck_config(self):
        """Show deck configuration"""
        try:
            dialog = DeckConfigDialog(self.config, self)
            dialog.exec()
        except Exception as e:
            # self.debug.log(f"Deck config error: {e}", True)
            pass

    def test_api_key(self):
        """Test API key"""
        lang = self.config.get("language", "vi")
        if not self.config["api_key"]:
            showInfo(get_text(lang, "api_key_missing"))
            return

        # self.debug.log("Testing API key...")
        result = self.call_gemini_api("Xin chào! Hãy trả lời ngắn gọn 'Kết nối thành công!'")

        if "Kết nối thành công" in result or "Success" in result or "success" in result:
            showInfo(get_text(lang, "api_test_success"))
            # self.debug.log("API test: SUCCESS")
        else:
            showInfo(get_text(lang, "api_test_failed", result=result))
            # self.debug.log(f"API test: FAILED - {result}")

    def cleanup(self):
        """Clean up resources"""
        try:
            self._cleanup_injected_elements() # Ensure cleanup on profile close
            if self.chat_window:
                self.chat_window.close() # Now chat_window.close() will hide the injected UI
                self.chat_window = None # Dereference the chat window
            # self.debug.log("Cleanup completed")
        except Exception as e:
            # self.debug.log(f"Cleanup error: {e}")
            pass