from aqt import mw
from aqt.qt import *
import re
import json
from aqt.utils import showInfo

from .debug_tools import DebugTools
from .languages import get_text


class GeminiThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, parent, history):
        super().__init__()
        self.parent = parent # This is the GeminiChatBot instance
        self.history = history

    def run(self):
        # Call the API through the parent (GeminiChatBot) instance
        response = self.parent.call_gemini_api(self.history)
        self.finished.emit(str(response))


class ChatWindow:
    """Phiên bản inject trực tiếp vào webview (không dùng QDialog)."""

    def __init__(self, parent):
        self.parent = parent # This is the GeminiChatBot instance
        self.debug = DebugTools("ChatWindow")
        self.thread = None
        self.conversation_history = [] 
        # self.debug.log("Initializing injected ChatWindow...")
        self.register_handlers()
        # self.inject_ui() # Don't inject on init, only when explicitly opened

    def register_handlers(self):
        """Register message handlers"""
        from aqt.gui_hooks import webview_did_receive_js_message
        webview_did_receive_js_message.append(self.handle_pycmd)
        # self.debug.log("PyCmd handlers registered")

    def handle_pycmd(self, handled, message, context):
        """Xử lý các lệnh được gửi từ JS qua pycmd()."""
        # self.debug.log(f"Bridge command received: {message}")

        if message == "gemini_chat_close":
            self.close()
            return True, None
        elif message == "gemini_chat_send_message":
            if mw.reviewer and mw.reviewer.web:
                js_get_input = """
                (function() {
                    var inputBox = document.getElementById('gemini-input-text');
                    var inputText = inputBox ? inputBox.value.trim() : '';
                    inputBox.value = ''; 
                    return inputText;
                })();
                """

                def got_input(prompt):
                    if prompt:  # Check not None or empty
                        self.send_message(prompt)
                        # self.add_message("user", prompt)

                mw.reviewer.web.evalWithCallback(js_get_input, got_input)
            return True, None

        return handled


    # ==================== UI INJECTION ====================
    def inject_ui(self):
        """Inject CSS + HTML vào reviewer và hiển thị nó."""
        
        # Localization
        lang = self.parent.config.get("language", "vi")
        
        self.t = {
            "header": get_text(lang, "header"),
            "placeholder": get_text(lang, "placeholder"),
            "send": get_text(lang, "send"),
            "typing": get_text(lang, "typing"),
            "welcome": get_text(lang, "welcome"),
            "you": get_text(lang, "you"),
            "ai": get_text(lang, "ai")
        }
        t = self.t

        # CSS và HTML cho cửa sổ chat
        # Sử dụng prefix #gemini-chat-container để isolate CSS tốt hơn
        css = """
        <style id="gemini-chat-style">
        /* Reset styles for our container to prevent inheritance */
        #gemini-chat-container, #gemini-chat-container * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        #gemini-chat-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 380px;
            height: 600px;
            background: #ffffff;
            border-radius: 24px;
            box-shadow: 0 12px 40px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.05);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            z-index: 99999;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            opacity: 0;
            transform: translateY(20px) scale(0.95);
            animation: gemini-fade-in 0.3s forwards;
        }

        @keyframes gemini-fade-in {
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        #gemini-chat-header {
            padding: 20px 24px;
            background: #ffffff;
            color: #1a1a1a;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 18px;
            border-bottom: 1px solid #f0f0f0;
            flex-shrink: 0;
        }

        #gemini-header-title {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        #gemini-header-title::before {
            content: '';
            display: block;
            width: 10px;
            height: 10px;
            background: #10a37f; /* OpenAI green-ish or any accent */
            border-radius: 50%;
        }

        #gemini-close-btn {
            background: transparent;
            border: none;
            color: #888;
            font-size: 24px;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.2s ease;
            line-height: 1;
        }
        #gemini-close-btn:hover {
            background: #f5f5f5;
            color: #333;
        }

        #gemini-chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #ffffff;
            word-wrap: break-word;
            display: flex;
            flex-direction: column;
            gap: 15px;
            scroll-behavior: smooth;
        }

        /* Scrollbar styling */
        #gemini-chat-messages::-webkit-scrollbar {
            width: 6px;
        }
        #gemini-chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }
        #gemini-chat-messages::-webkit-scrollbar-thumb {
            background-color: rgba(0,0,0,0.1);
            border-radius: 3px;
        }

        .message {
            text-align: left;
            max-width: 85%;
            line-height: 1.6;
            font-size: 15px;
            position: relative;
            word-break: break-word;
        }

        .user-message {
            align-self: flex-end;
            background: #007bff;
            color: #ffffff;
            border-radius: 18px 18px 4px 18px;
            padding: 12px 16px;
            box-shadow: 0 2px 5px rgba(0,123,255,0.2);
        }

        .bot-message {
            align-self: flex-start;
            background: #f1f3f4;
            color: #1f1f1f;
            border-radius: 18px 18px 18px 4px;
            padding: 12px 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        /* Markdown styling within bot messages */
        .bot-message b { font-weight: 600; color: #000; }
        .bot-message i { font-style: italic; }
        .bot-message code {
            background: #e0e0e0;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: 'Menlo', 'Consolas', monospace;
            font-size: 0.9em;
            color: #d63384;
        }
        .bot-message pre {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 8px 0;
            border: 1px solid #eee;
        }

        #gemini-chat-input-area {
            padding: 20px;
            background: #ffffff;
            border-top: 1px solid #f0f0f0;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        #gemini-input-wrapper {
            display: flex;
            align-items: center;
            background: #f4f4f4;
            border-radius: 24px;
            padding: 4px 4px 4px 16px;
            border: 1px solid transparent;
            transition: all 0.2s ease;
        }
        
        #gemini-input-wrapper:focus-within {
            background: #ffffff;
            border-color: #ddd;
            box-shadow: 0 0 0 2px rgba(0,0,0,0.05);
        }

        #gemini-input-text {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            padding: 8px 0;
            font-size: 15px;
            color: #333;
            min-width: 0;
        }

        #gemini-send-btn {
            background: #1a1a1a;
            color: white;
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.2s ease;
            flex-shrink: 0;
            margin-left: 8px;
        }

        #gemini-send-btn:hover {
            background: #333;
            transform: scale(1.05);
        }
        
        #gemini-send-btn svg {
            width: 18px;
            height: 18px;
            fill: white;
        }

        #gemini-typing {
            font-size: 12px;
            color: #999;
            margin-left: 16px;
            height: 16px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        #gemini-typing.visible {
            opacity: 1;
        }
        </style>
        """

        html_content = css + f"""
        <div id="gemini-chat-container">
            <div id="gemini-chat-header">
                <div id="gemini-header-title">{t['header']}</div>
                <button id="gemini-close-btn" onclick="pycmd('gemini_chat_close')">×</button>
            </div>
            <div id="gemini-chat-messages"></div>
            <div id="gemini-chat-input-area">
                <div id="gemini-typing">{t['typing']}</div>
                <div id="gemini-input-wrapper">
                    <input id="gemini-input-text" type="text" placeholder="{t['placeholder']}"
           onkeypress="if(event.key==='Enter'){{pycmd('gemini_chat_send_message'); event.preventDefault();}}" />
                    <button id="gemini-send-btn" onclick="pycmd('gemini_chat_send_message')">
                        <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path></svg>
                    </button>
                </div>
            </div>
        </div>

        <script>
        // Ensure chat is visible when injected
        var chatContainer = document.getElementById('gemini-chat-container');
        if (chatContainer) {{
            chatContainer.style.display = 'flex';
            chatContainer.querySelector('#gemini-input-text').focus(); // Focus input
        }}
        </script>
        """

        reviewer = mw.reviewer.web
        js_code_to_inject = f"""
        (function() {{
            var existingChatContainer = document.getElementById('gemini-chat-container');
            if (existingChatContainer) {{
                existingChatContainer.style.display = 'flex'; // Just show it if already exists
                existingChatContainer.querySelector('#gemini-input-text').focus();
            }} else {{
                document.body.insertAdjacentHTML('beforeend', `{html_content}`);
            }}
            console.log('Gemini Chat Window injected/shown successfully');
        }})();
        """
        reviewer.eval(js_code_to_inject)
        # self.debug.log("Injected chat UI successfully")
        # Add an initial greeting from the bot when the chat window is opened
        if mw.reviewer and mw.reviewer.web:
            js_check = f"""
            (function() {{
                const msgs = document.querySelectorAll('.bot-message');
                for (let m of msgs) {{
                    if (m.innerText.includes("{t['welcome']}")) {{
                        return true; // already exists
                    }}
                }}
                return false;
            }})();
            """

            def callback(exists):
                if not exists:
                    self.add_message("bot", t['welcome'])

            mw.reviewer.web.evalWithCallback(js_check, callback)

    def close(self):
        """Ẩn cửa sổ chat."""
        # self.debug.log(f"Has reviewer web: {bool(mw.reviewer and mw.reviewer.web)}")
        # self.debug.log(f"Has mw.web: {bool(mw.web)}")

        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("""
            var chatContainer = document.getElementById('gemini-chat-container');
            if (chatContainer){
                chatContainer.style.display = 'none';
            } else {
                console.log('Gemini Chat Container not found to hide.');
            }
            """)
        else:
            # fallback: dùng context trực tiếp nếu có
            try:
                context.web.eval("""
                var chatContainer = document.getElementById('gemini-chat-container');
                if (chatContainer) chatContainer.style.display = 'none';
                """)
            except:
                pass
        # self.debug.log("Chat window hidden instantly via bridge command.")


    # ==================== MESSAGE HANDLING ====================
    def add_message(self, sender, message):
        """Thêm tin nhắn vào DOM"""
        # Escape backticks and dollar signs for JavaScript template literals
        # showInfo(f"Adding message: [{sender}] {message[:50]}...")
        if message is None:
            return
        
        # Use stored translations or fallback
        t = getattr(self, 't', {"you": "Bạn", "ai": "AI"})
        
        safe_message = message.replace("`", "\\`").replace("${", "\\${}")
        if sender == "user":
            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                m.innerHTML += `<div class='message user-message'><b>{t['you']}:</b> {safe_message}</div>`;
                m.scrollTop = m.scrollHeight;
            }}
            """
            mw.reviewer.web.eval(js)
        else:
            # Bot message - xử lý markdown cơ bản
            # Bold
            safe_message = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_message)
            # Italic
            safe_message = re.sub(r'\*(.*?)\*', r'<i>\1</i>', safe_message)
            # Code block (đơn giản)
            safe_message = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', safe_message, flags=re.DOTALL)
            # Inline code
            safe_message = re.sub(r'`(.*?)`', r'<code>\1</code>', safe_message)
            # Newlines
            safe_message = safe_message.replace('\n', '<br>')

            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                m.innerHTML += `<div class='message bot-message'><div class='bot-message-content'><b>{t['ai']}:</b> {safe_message}</div></div>`;
                m.scrollTop = m.scrollHeight;
            }}
            """
            mw.reviewer.web.eval(js)

    def pre_fill_input(self, text):
        """Điền sẵn text vào ô input."""
        if not text:
            # If text is empty, clear the input
            js = """
            var input = document.getElementById('gemini-input-text');
            if (input) input.value = '';
            """
        else:
            safe_text = text.replace("`", "\\`").replace("${", "\\${}")
            js = f"""
            var input = document.getElementById('gemini-input-text');
            if (input) input.value = `{safe_text}`;
            """
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval(js)

    def send_message(self, message):
        """Gửi tin nhắn đến Gemini."""
        # 1. Hiển thị tin nhắn user
        self.add_message("user", message)
        
        # 2. Hiển thị typing indicator
        self.show_typing()

        # 3. Cập nhật lịch sử
        self.conversation_history.append({"role": "user", "parts": [message]})

        # 4. Gọi API (trong thread riêng để không chặn UI)
        self.thread = GeminiThread(self.parent, self.conversation_history)
        self.thread.finished.connect(self.on_api_response)
        self.thread.start()

    def on_api_response(self, response):
        """Xử lý phản hồi từ API."""
        self.hide_typing()
        self.add_message("bot", response)
        self.conversation_history.append({"role": "model", "parts": [response]})

    def show_typing(self):
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("document.getElementById('gemini-typing').classList.add('visible');")

    def hide_typing(self):
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("document.getElementById('gemini-typing').classList.remove('visible');")
