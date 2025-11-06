from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .debug_tools import DebugTools


class GeminiThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, parent, prompt):
        super().__init__()
        self.parent = parent # This is the GeminiChatBot instance
        self.prompt = prompt

    def run(self):
        # Call the API through the parent (GeminiChatBot) instance
        response = self.parent.call_gemini_api(self.prompt)
        self.finished.emit(str(response))


class ChatWindow:
    """Phiên bản inject trực tiếp vào webview (không dùng QDialog)."""

    def __init__(self, parent):
        self.parent = parent # This is the GeminiChatBot instance
        self.debug = DebugTools("ChatWindow")
        self.thread = None
        self.debug.log("Initializing injected ChatWindow...")
        self.register_handlers()
        # self.inject_ui() # Don't inject on init, only when explicitly opened

    def register_handlers(self):
        """Register message handlers"""
        from aqt.gui_hooks import webview_did_receive_js_message
        webview_did_receive_js_message.append(self.handle_pycmd)
        self.debug.log("PyCmd handlers registered")

    def handle_pycmd(self, handled, message, context):
        """Xử lý các lệnh được gửi từ JS qua pycmd()."""
        self.debug.log(f"Bridge command received: {message}")

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

        return handled, None


    # ==================== UI INJECTION ====================
    def inject_ui(self):
        """Inject CSS + HTML vào reviewer và hiển thị nó."""
        # CSS và HTML cho cửa sổ chat (không bao gồm nút bấm mở chat)
        css = """
        <style id="gemini-chat-style">
        #gemini-chat-container {
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 320px;
            height: 400px;
            background: #ffffffee;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            display: flex; /* Set to flex by default, then toggle visibility via JS */
            flex-direction: column;
            overflow: hidden;
            z-index: 99999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            border: 1px solid rgba(0,0,0,0.1); /* subtle border */
        }
        #gemini-chat-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 10px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
        }
        #gemini-close-btn {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            line-height: 1;
            padding: 0 5px;
        }
        #gemini-close-btn:hover {
            opacity: 0.8;
        }
        #gemini-chat-messages {
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            background: #f9f9fb;
            word-wrap: break-word; /* Ensure long words wrap */
        }
        .message {
            margin: 8px 0;
            line-height: 1.4em;
        }
        .user-message {
            text-align: right;
            color: #333;
        }
        .bot-message {
            text-align: left;
            color: #222;
            background: #eef1ff;
            border-radius: 8px;
            padding: 6px 10px;
            display: inline-block;
            max-width: 85%; /* Limit width to make it look like a bubble */
        }
        #gemini-chat-input {
            display: flex;
            border-top: 1px solid #ddd;
            padding: 5px;
            background: #ffffff;
        }
        #gemini-input-text {
            flex: 1;
            padding: 8px;
            border: 1px solid #eee;
            border-radius: 5px;
            outline: none;
            font-size: 14px;
        }
        #gemini-input-text:focus {
            border-color: #667eea;
        }
        #gemini-send-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            margin-left: 5px;
            transition: background 0.3s ease;
            font-size: 14px;
        }
        #gemini-send-btn:hover {
            background: #764ba2;
        }
        #gemini-typing {
            font-style: italic;
            opacity: 0.7;
        }
        </style>
        """

        html_content = css + """
        <div id="gemini-chat-container">
            <div id="gemini-chat-header">
                Gemini ChatBot
                <button id="gemini-close-btn" onclick="pycmd('gemini_chat_close')">×</button>
            </div>
            <div id="gemini-chat-messages"></div>
            <div id="gemini-chat-input">
                <input id="gemini-input-text" type="text" placeholder="Nhập tin nhắn..."
       onkeypress="if(event.key==='Enter'){pycmd('gemini_chat_send_message'); event.preventDefault();}" />
                <button id="gemini-send-btn" onclick="pycmd('gemini_chat_send_message')">Gửi</button>
            </div>
        </div>

        <script>
        // Ensure chat is visible when injected
        var chatContainer = document.getElementById('gemini-chat-container');
        if (chatContainer) {
            chatContainer.style.display = 'flex';
            chatContainer.querySelector('#gemini-input-text').focus(); // Focus input
        }
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
                // Initial message from AI when chat opens
                // pycmd('gemini_chat_send:Chào bạn, tôi là Gemini ChatBot. Tôi có thể giúp gì cho bạn?');
            }}
            console.log('Gemini Chat Window injected/shown successfully');
        }})();
        """
        reviewer.eval(js_code_to_inject)
        self.debug.log("Injected chat UI successfully")
        # Add an initial greeting from the bot when the chat window is opened
        if mw.reviewer and mw.reviewer.web:
            self.add_message("bot", "Chào bạn, tôi là Gemini ChatBot. Tôi có thể giúp gì cho bạn?")

    def close(self):
        """Ẩn cửa sổ chat."""
        self.debug.log(f"Has reviewer web: {bool(mw.reviewer and mw.reviewer.web)}")
        self.debug.log(f"Has mw.web: {bool(mw.web)}")

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
        self.debug.log("Chat window hidden instantly via bridge command.")


    # ==================== MESSAGE HANDLING ====================
    def add_message(self, sender, message):
        """Thêm tin nhắn vào DOM"""
        # Escape backticks and dollar signs for JavaScript template literals
        # showInfo(f"Adding message: [{sender}] {message[:50]}...")
        if message is None:
            return
        safe_message = message.replace("`", "\\`").replace("${", "\\${}")
        if sender == "user":
            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                m.innerHTML += `<div class='message user-message'><b>Bạn:</b> {safe_message}</div>`;
                m.scrollTop = m.scrollHeight;
            }}
            """
        else: # bot message
            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                m.innerHTML += `<div class='message bot-message'><b>AI:</b> {safe_message}</div>`;
                m.scrollTop = m.scrollHeight;
            }}
            """
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval(js)
            self.debug.log(f"Added message: [{sender}] {message[:50]}...")

    def show_typing(self):
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                var existingTyping = document.getElementById('gemini-typing');
                if (!existingTyping) {{ // Only add if not already present
                    m.innerHTML += "<div id='gemini-typing' class='message bot-message'><em>AI đang trả lời...</em></div>";
                    m.scrollTop = m.scrollHeight;
                }}
            }}
            """)
            self.debug.log("Showing typing indicator.")

    def hide_typing(self):
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("""
            var t = document.getElementById('gemini-typing');
            if (t) t.remove();
            """)
            self.debug.log("Hiding typing indicator.")

    # ==================== LOGIC ====================
    def send_message(self, text):
        """Gửi prompt đến Gemini"""
        if not text:
            return
        self.add_message("user", text)
        self.show_typing()
        self.debug.log(f"Starting GeminiThread for prompt: {text[:50]}...")

        # Kill existing thread if it's running
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait() # Wait for it to finish gracefully
            self.debug.log("Terminated previous GeminiThread.")

        self.thread = GeminiThread(self.parent, text)
        self.thread.finished.connect(self.handle_response)
        self.thread.start()

    def handle_response(self, response):
        self.hide_typing()
        self.add_message("bot", response)
        self.debug.log(f"Received response from Gemini: {response}")