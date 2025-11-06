from aqt import mw
from aqt.qt import *
import re
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

        return handled


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
            width: 350px; /* Slightly wider */
            height: 500px; /* Slightly taller */
            background: #ffffff;
            border-radius: 16px; /* More rounded corners */
            box-shadow: 0 10px 30px rgba(0,0,0,0.15); /* Softer, more prominent shadow */
            display: flex;
            flex-direction: column;
            overflow: hidden;
            z-index: 99999;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; /* Modern font stack */
            border: none; /* Remove subtle border for cleaner look */
        }
        #gemini-chat-header {
            padding-left: 25px;
            background: linear-gradient(135deg, #4A90E2, #5D5BD9); /* Brighter, more vibrant blue gradient */
            color: white;
            font-weight: 600; /* Slightly bolder */
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 18px; /* Larger font size */
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        }
        #gemini-close-btn {
            background: rgba(255, 255, 255, 0.2); /* Semi-transparent white background */
            border: none;
            color: white;
            font-size: 20px; /* Smaller font size for 'x' */
            width: 30px; /* Fixed width */
            height: 30px; /* Fixed height */
            aspect-ratio: 1 / 1;
            border-radius: 50% !important;
            cursor: pointer;
            display: flex; /* Use flex to center 'x' */
            justify-content: center; /* Center horizontally */
            align-items: center; /* Center vertically */
            transition: background 0.2s ease-in-out, transform 0.2s ease-in-out; /* Smooth transitions */
            line-height: 1; /* Ensure 'x' is vertically centered */
        }
        #gemini-close-btn:hover {
            background: rgba(255, 255, 255, 0.35); /* Darker on hover */
        }
        #gemini-close-btn:active {
            background: rgba(255, 255, 255, 0.45);
        }
        .message b {
            font-weight: 700; /* Hoặc 'bold'. 700 là một giá trị số phổ biến cho in đậm */
        }
        .message i {
            font-style: italic; /* Đảm bảo kiểu chữ là nghiêng */
        }
        #gemini-chat-messages {
            flex: 1;
            padding: 15px; /* More padding */
            overflow-y: auto;
            background: #F0F2F5; /* Lighter background for messages */
            word-wrap: break-word;
            display: flex; /* Make messages a flex container */
            flex-direction: column; /* Stack messages vertically */
        }
        .message {
            margin: 10px 0; /* More vertical spacing */
            line-height: 1.4em; /* Improved readability */
            font-size: 16px;
        }
        .user-message {
            align-self: flex-end; /* Pushes message to the right */
            background: #EBF5FF; /* Light blue bubble for user */
            border-radius: 12px 12px 2px 12px; /* Nicer bubble shape */
            text-align: left;
            padding: 8px 12px;
            max-width: 80%;
            color: #333;
            box-shadow: 0 1px 2px rgba(0,0,0,0.08); /* Subtle shadow for bubbles */
        }
        .bot-message {
            align-self: flex-start; /* Pushes message to the left */
            text-align: left;
            background: #FFFFFF; /* White bubble for bot */
            border-radius: 12px 12px 12px 2px; /* Nicer bubble shape */
            padding: 8px 12px;
            max-width: 80%; /* Limit width to make it look like a bubble */
            color: #222;
            box-shadow: 0 1px 2px rgba(0,0,0,0.08); /* Subtle shadow for bubbles */
        }
        #gemini-chat-input {
            display: flex;
            border-top: 1px solid #E0E0E0; /* Lighter border */
            padding: 10px 15px; /* More padding */
            background: #ffffff;
            align-items: center; /* Vertically align items */
            gap: 10px; /* Space between input and button */
        }
        #gemini-input-text {
            flex: 1;
            padding: 10px 12px; /* More padding */
            border: 1px solid #D0D0D0; /* Lighter border */
            border-radius: 20px; /* Pill-shaped input */
            outline: none;
            text-align: left;
            font-size: 15px;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        #gemini-input-text:focus {
            border-color: #4A90E2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2); /* Focus glow */
        }
        #gemini-send-btn {
            background: #4A90E2; /* Solid blue send button */
            color: white;
            border: none;
            padding: 10px 20px; /* More padding for button */
            border-radius: 20px; /* Pill-shaped button */
            cursor: pointer;
            transition: background 0.3s ease, transform 0.2s ease;
            font-size: 15px;
            font-weight: 500;
            white-space: nowrap; /* Prevent text wrapping */
        }
        #gemini-send-btn:hover {
            background: #5D5BD9; /* Darker blue on hover */
            transform: translateY(-1px); /* Slight lift effect */
        }
        #gemini-send-btn:active {
            transform: translateY(0); /* Press effect */
        }
        #gemini-typing {
            font-style: italic;
            opacity: 0.8;
            padding: 5px 15px;
            color: #666;
            font-size: 13px;
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
            <div id="gemini-typing" style="display:none;">Gemini đang gõ...</div>
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
        # self.debug.log("Injected chat UI successfully")
        # Add an initial greeting from the bot when the chat window is opened
        if mw.reviewer and mw.reviewer.web:
            js_check = """
            (function() {
                const msgs = document.querySelectorAll('.bot-message');
                for (let m of msgs) {
                    if (m.innerText.includes("Chào bạn, tôi là Gemini ChatBot")) {
                        return true; // already exists
                    }
                }
                return false;
            })();
            """

            def callback(exists):
                if not exists:
                    self.add_message("bot", "Chào bạn, tôi là Gemini ChatBot. Tôi có thể giúp gì cho bạn?")

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
            self.debug.log(f"message before formatting: {safe_message[:]}...")
            def format_markdown(text):
                # ***text*** → <b><i>text</i></b>
                text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", text)

                # **text** → <b>text</b>
                text = re.sub(r"(?<!\*)\*\*(?!\*)(.*?)\*\*(?!\*)", r"<b>\1</b>", text)

                # *text* → <i>text</i> 
                # (không ăn vào dấu * trong bullet list hoặc khoảng trắng)
                text = re.sub(r"(?<!\S)\*(?!\*)([^\*]+?)\*(?!\S)", r"<i>\1</i>", text)

                # Chuyển xuống dòng thành <br>
                text = text.replace("\n", "<br>")

                # Loại bỏ khoảng trắng dư quanh <br>
                text = re.sub(r"\s*<br>\s*", "<br>", text)

                return text

            safe_message = format_markdown(safe_message)
            self.debug.log(f"message after formatting: {safe_message[:]}...")
            js = f"""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                m.innerHTML += `<div class='message bot-message'><b>AI:</b> {safe_message}</div>`;
                m.scrollTop = m.scrollHeight;
            }}
            """
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval(js)
            # self.debug.log(f"Added message: [{sender}] {message[:50]}...")

    def show_typing(self):
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("""
            var m = document.getElementById('gemini-chat-messages');
            if (m) {{
                var existingTyping = document.getElementById('gemini-typing');
                if (!existingTyping) {{ 
                    m.innerHTML += "<div id='gemini-typing' class='message bot-message'><em>AI đang trả lời...</em></div>";
                    m.scrollTop = m.scrollHeight;
                }}
            }}
            """)
            # self.debug.log("Showing typing indicator.")

    def hide_typing(self):
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval("""
            var t = document.getElementById('gemini-typing');
            if (t) t.remove();
            """)
            # self.debug.log("Hiding typing indicator.")

    # ==================== LOGIC ====================
    def send_message(self, text):
        """Gửi prompt đến Gemini"""
        if not text:
            return
        self.add_message("user", text)
        self.show_typing()
        # self.debug.log(f"Starting GeminiThread for prompt: {text[:50]}...")

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
        # self.debug.log(f"Received response from Gemini: {response}")
    
    def pre_fill_input(self, text):
        """Prefill input only if this exact prompt has NOT been asked before."""
        self.debug.log(f"Attempting to pre-fill with: {text[:50]}...")

        if not text:
            return

        safe = text.replace("`", "\\`").replace("${", "\\${}")

        js = f"""
        (function() {{
            var msgs = document.querySelectorAll('.user-message');
            for (let m of msgs) {{
                if (m.innerText.trim() === `Bạn: {safe}`.trim()) {{
                    console.log('Prefill skipped: prompt already asked.');
                    return false;   // already asked → skip prefill
                }}
            }}

            var input = document.getElementById('gemini-input-text');
            if (input) {{
                input.value = `{safe}`;
            }}
            return true; // did prefill
        }})();
        """

        def callback(result):
            if result:
                self.debug.log("Prefilled input successfully.")
            else:
                self.debug.log("Skipped prefill (already asked).")

        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.evalWithCallback(js, callback)

