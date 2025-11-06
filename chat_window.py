from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .debug_tools import DebugTools


class GeminiThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, parent, prompt):
        super().__init__()
        self.parent = parent
        self.prompt = prompt

    def run(self):
        response = self.parent.call_gemini_api(self.prompt)
        self.finished.emit(str(response))


class ChatWindow:
    """Phiên bản inject trực tiếp vào webview (không dùng QDialog)."""

    def __init__(self, parent):
        self.parent = parent
        self.debug = DebugTools("ChatWindow")
        self.thread = None
        self.debug.log("Initializing injected ChatWindow...")
        self.inject_ui()

    # ==================== UI INJECTION ====================
    def inject_ui(self):
        """Inject CSS + HTML vào reviewer"""
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
            display: block;
            flex-direction: column;
            overflow: hidden;
            z-index: 99999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #gemini-chat-header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 10px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        #gemini-chat-messages {
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            background: #f9f9fb;
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
        }
        #gemini-chat-input {
            display: flex;
            border-top: 1px solid #ddd;
        }
        #gemini-input-text {
            flex: 1;
            padding: 8px;
            border: none;
            outline: none;
        }
        #gemini-send-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0 16px;
            cursor: pointer;
        }
        #gemini-chatbot-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-size: 22px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            z-index: 99998;
        }
        #gemini-chatbot-btn:hover {
            transform: scale(1.05);
        }
        </style>
        """

        html = css + """
        <div id="gemini-chat-container">
            <div id="gemini-chat-header">
                Gemini ChatBot
                <button id="gemini-close-btn">×</button>
            </div>
            <div id="gemini-chat-messages"></div>
            <div id="gemini-chat-input">
                <input id="gemini-input-text" type="text" placeholder="Nhập tin nhắn..." />
                <button id="gemini-send-btn">Gửi</button>
            </div>
        </div>

        <script>
        // Toggle chat visibility
        document.getElementById('gemini-chatbot-btn').onclick = function() {
            const chat = document.getElementById('gemini-chat-container');
            chat.style.display = (chat.style.display === 'flex') ? 'none' : 'flex';
        };
        document.getElementById('gemini-close-btn').onclick = function() {
            document.getElementById('gemini-chat-container').style.display = 'none';
        };

        // Send message event
        document.getElementById('gemini-send-btn').onclick = function() {
            const text = document.getElementById('gemini-input-text').value.trim();
            if (text) {
                pycmd('gemini_chat_send:' + text);
            }
        };

        // Enter key to send
        document.getElementById('gemini-input-text').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('gemini-send-btn').click();
            }
        });
        </script>
        """

        reviewer = mw.reviewer.web
        reviewer.eval(f"""
        (function() {{
            var existing = document.getElementById('gemini-chat-container');
            if (existing) existing.remove();
            var btn = document.getElementById('gemini-chatbot-btn');
            if (btn) btn.remove();
            document.body.insertAdjacentHTML('beforeend', `{html}`);
        }})();
        """)
        self.debug.log("Injected chat UI successfully")

    # ==================== MESSAGE HANDLING ====================
    def add_message(self, sender, message):
        """Thêm tin nhắn vào DOM"""
        safe_message = message.replace("`", "\\`").replace("${", "\\${}")
        if sender == "user":
            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            m.innerHTML += `<div class='message user-message'><b>Bạn:</b> {safe_message}</div>`;
            m.scrollTop = m.scrollHeight;
            """
        else:
            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            m.innerHTML += `<div class='message bot-message'><b>AI:</b> {safe_message}</div>`;
            m.scrollTop = m.scrollHeight;
            """
        mw.reviewer.web.eval(js)

    def show_typing(self):
        mw.reviewer.web.eval("""
        var m = document.getElementById('gemini-chat-messages');
        m.innerHTML += "<div id='gemini-typing' class='message bot-message'><em>AI đang trả lời...</em></div>";
        m.scrollTop = m.scrollHeight;
        """)

    def hide_typing(self):
        mw.reviewer.web.eval("""
        var t = document.getElementById('gemini-typing');
        if (t) t.remove();
        """)

    # ==================== LOGIC ====================
    def send_message(self, text):
        """Gửi prompt đến Gemini"""
        if not text:
            return
        self.add_message("user", text)
        self.show_typing()
        self.thread = GeminiThread(self.parent, text)
        self.thread.finished.connect(self.handle_response)
        self.thread.start()

    def handle_response(self, response):
        self.hide_typing()
        self.add_message("bot", response)
