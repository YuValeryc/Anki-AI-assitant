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


class GeminiChatBot:
    def __init__(self):
        self.debug = DebugTools("GeminiChatBot")
        self.debug.log("Initializing GeminiChatBot...")

        self.config = self.load_config()
        self.current_card = None
        self.chat_window: ChatWindow = None # Type hint for better clarity

        self.setup_menu()
        self.register_handlers()
        self.register_hooks()

        self.debug.log("GeminiChatBot initialized successfully", True)

    def register_handlers(self):
        """Register message handlers"""
        from aqt.gui_hooks import webview_did_receive_js_message
        webview_did_receive_js_message.append(self.handle_pycmd)
        self.debug.log("PyCmd handlers registered")

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

        self.debug.log(f"Registered {len(hooks)} hooks")

    def on_state_change(self, new_state, old_state):
        """Debug state changes"""
        self.debug.log(f"State change: {old_state} → {new_state}")
        if old_state == "review" and new_state != "review":
            self.debug.log("Leaving review → cleaning UI")
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

        self.debug.log(f"PyCmd received: {cmd}")

        if cmd == "gemini_chat_open":
            self.open_chat_window()
            return (True, None)
        elif cmd.startswith("gemini_chat_send:"):
            message = cmd.split(":", 1)[1]
            if self.chat_window:
                self.chat_window.send_message(message)
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
            # Deep merge
            config = default_config.copy()
            config.update(user_config)
            config["custom_prompts"] = {**default_config["custom_prompts"], **user_config.get("custom_prompts", {})}

            self.debug.log("Configuration loaded successfully")
            return config

        except Exception as e:
            self.debug.log(f"Config load error: {e}", True)
            return default_config

    def save_config(self):
        """Save configuration"""
        try:
            mw.addonManager.writeConfig(__name__, self.config)
            self.debug.log("Configuration saved")
        except Exception as e:
            self.debug.log(f"Config save error: {e}", True)

    def setup_menu(self):
        """Add menu items"""
        try:
            menu = QMenu("Gemini ChatBot", mw)

            actions = [
                ("Cấu hình ChatBot", self.show_config_dialog),
                ("Cài đặt theo Deck", self.show_deck_config),
                ("Test API Key", self.test_api_key),
                ("Debug Info", self.show_debug_info)
            ]

            for name, handler in actions:
                action = QAction(name, mw)
                action.triggered.connect(handler)
                menu.addAction(action)

            mw.form.menuTools.addMenu(menu)
            self.debug.log("Menu setup completed")

        except Exception as e:
            self.debug.log(f"Menu setup error: {e}", True)

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
            self.debug.log("=== on_show_question TRIGGERED ===")
            self.debug.log(self.debug.inspect_card(card))

            # Remove existing chat UI and button on new card
            self._cleanup_injected_elements()

            # Check if addon is enabled
            if not self.config["enabled"]:
                self.debug.log("Addon disabled in config")
                return

            # Check if reviewer and webview are ready
            if not mw.reviewer or not mw.reviewer.web:
                self.debug.log("Reviewer or WebView not ready")
                return

            self.current_card = card

            # Get deck settings
            deck_id = str(card.did)
            deck_settings = self.config["deck_settings"].get(deck_id, {})
            deck_enabled = deck_settings.get("enabled", True)

            if not deck_enabled:
                self.debug.log(f"ChatBot disabled for deck {deck_id}")
                return

            # Get target field text
            target_field = deck_settings.get("target_field", self.config["target_field"])
            field_text = self.get_field_text(card, target_field)

            if not field_text.strip():
                self.debug.log(f"Empty field text for field: {target_field}")
                return

            # Get prompt template
            prompt_key = deck_settings.get("selected_prompt", self.config["selected_prompt"])
            prompt_template = self.config["custom_prompts"].get(prompt_key, "Bạn có muốn biết thêm về: {text}")

            self.debug.log(f"Showing button for: {field_text[:30]}...")
            self.show_chatbot_button(field_text, prompt_template)

        except Exception as e:
            self.debug.log(f"Error in on_show_question: {e}", True)

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
            # Format prompt text for tooltip
            display_text = text[:50] + "..." if len(text) > 50 else text
            formatted_prompt = prompt.format(text=display_text)

            # CSS với !important để override Anki styles
            css = """
            <style>
            #gemini-chatbot-btn {
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                width: 50px !important;
                height: 50px !important;
                background: linear-gradient(135deg, #4A90E2, #5D5BD9) !important;
                border-radius: 50% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                color: white !important;
                font-size: 20px !important;
                cursor: pointer !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
                z-index: 10000 !important;
                transition: all 0.3s ease !important;
                border: none !important;
            }
            #gemini-chatbot-btn:hover {
                transform: scale(1.1) !important;
                box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
            }
            .gemini-tooltip {
                position: fixed !important;
                bottom: 80px !important;
                right: 20px !important;
                background: rgba(0,0,0,0.9) !important;
                color: white !important;
                padding: 10px 14px !important;
                border-radius: 10px !important;
                font-size: 13px !important;
                max-width: 250px !important;
                z-index: 10001 !important;
                backdrop-filter: blur(10px) !important;
                border: 1px solid rgba(255,255,255,0.1) !important;
            }
            </style>
            """

            html = f"""
            {css}
            <div id="gemini-chatbot-tooltip-container">
                <div class="gemini-tooltip">{formatted_prompt}</div>
                <button id="gemini-chatbot-btn" onclick="pycmd('gemini_chat_open')">
                    🤖
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
            self.debug.log("ChatBot button injected successfully")

        except Exception as e:
            self.debug.log(f"Error showing chatbot button: {e}", True)

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
            self.debug.log("Cleaned up injected chat UI elements.")

    def on_review_end(self):
        """Clean up when review ends"""
        try:
            self._cleanup_injected_elements()
            self.debug.log("Review ended - cleanup completed")
        except Exception as e:
            self.debug.log(f"Cleanup error: {e}")

    def open_chat_window(self):
        """Open chat window"""
        self.debug.log("Opening chat window...")

        if not self.current_card:
            showInfo("Không có card nào đang active!")
            return

        if not self.config["api_key"]:
            showInfo("Vui lòng cấu hình API Key trong menu Tools → Gemini ChatBot → Cấu hình")
            return

        try:
            # Initialize chat_window if it doesn't exist
            if self.chat_window is None:
                self.chat_window = ChatWindow(self)

            self.chat_window.inject_ui()

            # ====== TẠO PROMPT TỰ ĐỘNG ======
            deck_id = str(self.current_card.did)
            deck_settings = self.config["deck_settings"].get(deck_id, {})
            self.debug.log(f"Deck settings for chat window: {deck_settings}")

            target_field = deck_settings.get("target_field")
            self.debug.log(f"Target field: {target_field}")

            # ✅ Lấy content của field
            card_content = self.get_field_text(self.current_card, target_field)
            self.debug.log(f"Field value: {card_content}")

            # ✅ Lấy prompt KEY trước
            prompt_key = deck_settings.get("selected_prompt") \
                        or self.config.get("selected_prompt")

            self.debug.log(f"Prompt key selected: {prompt_key}")

            # ✅ Lookup từ custom_prompts
            prompt_template = self.config["custom_prompts"].get(prompt_key)

            # Nếu prompt không nằm trong custom_prompt → dùng default
            if not prompt_template:
                prompt_template = "Giải thích về: {text}"

            self.debug.log(f"Resolved prompt template: {prompt_template}")

            # ✅ Tạo auto prompt
            auto_prompt = prompt_template.replace("{text}", card_content)
            self.debug.log(f"Auto prompt generated: {auto_prompt}")

            # ✅ Đưa sẵn vào ô input
            self.chat_window.pre_fill_input(auto_prompt)
            self.debug.log("Chat window injected/shown successfully")

        except Exception as e:
            showInfo(f"Lỗi khi inject chat window: {e}")
            self.debug.log(f"Error opening chat window: {e}", True)

    def call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API với error handling"""
        if not self.config.get("api_key"):
            return "❌ Lỗi: Chưa cấu hình API Key"

        api_key = self.config.get("api_key")
        # Sử dụng gemini-pro cho khả năng tốt hơn, gemini-2.0-flash không tồn tại trong API công khai
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": self.config.get("max_tokens", 500),
                "temperature": 0.7,
            }
        }

        self.debug.log("Calling Gemini API...")

        # retry on 429 (rate limit) with exponential backoff
        max_attempts = 3
        backoff = 1.0
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(url, json=payload, timeout=30)
                # self.debug.log(f"Response: {response.status_code} - {response.text}")
                if response.status_code == 429:
                    self.debug.log(f"Gemini API rate-limited (429). Attempt {attempt}/{max_attempts}")
                    if attempt < max_attempts:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    else:
                        return "❌ Lỗi Gemini: Quá nhiều yêu cầu (rate limited). Hãy thử lại sau"
                response.raise_for_status()

                result = response.json()

                # Safely extract response text
                response_text = ""
                try:
                    response_text = result.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
                except (IndexError, TypeError): # Handle cases where candidates or content might be missing
                    # If text is not found, try to return error message from API
                    error_message = result.get("error", {}).get("message", str(result))
                    self.debug.log(f"Gemini API response parsing error, full result: {result}")
                    return f"❌ Lỗi Gemini: {error_message}"

                self.debug.log("Gemini API call successful")
                return response_text

            except requests.exceptions.RequestException as e:
                self.debug.log(f"Gemini API network error (attempt {attempt}): {e}")
                if attempt < max_attempts:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return f"❌ Lỗi kết nối Gemini: {e}"
            except Exception as e:
                self.debug.log(f"Gemini API unexpected error: {e}", True)
                return f"❌ Lỗi Gemini nội bộ: {e}"

    def show_config_dialog(self):
        """Show configuration dialog"""
        try:
            dialog = ConfigDialog(self.config, self)
            if dialog.exec():
                self.config = dialog.get_config()
                self.save_config()
                showInfo("Cấu hình đã được lưu!")
        except Exception as e:
            self.debug.log(f"Config dialog error: {e}", True)

    def show_deck_config(self):
        """Show deck configuration"""
        try:
            dialog = DeckConfigDialog(self.config, self)
            dialog.exec()
        except Exception as e:
            self.debug.log(f"Deck config error: {e}", True)

    def test_api_key(self):
        """Test API key"""
        if not self.config["api_key"]:
            showInfo("Chưa có API Key!")
            return

        self.debug.log("Testing API key...")
        result = self.call_gemini_api("Xin chào! Hãy trả lời ngắn gọn 'Kết nối thành công!'")

        if "Kết nối thành công" in result:
            showInfo("✅ API Key hoạt động tốt!")
            self.debug.log("API test: SUCCESS")
        else:
            showInfo("❌ Lỗi API Key: " + result)
            self.debug.log(f"API test: FAILED - {result}")

    def cleanup(self):
        """Clean up resources"""
        try:
            self._cleanup_injected_elements() # Ensure cleanup on profile close
            if self.chat_window:
                self.chat_window.close() # Now chat_window.close() will hide the injected UI
                self.chat_window = None # Dereference the chat window
            self.debug.log("Cleanup completed")
        except Exception as e:
            self.debug.log(f"Cleanup error: {e}")