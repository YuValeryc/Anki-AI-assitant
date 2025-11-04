from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView

from .debug_tools import DebugTools


class GeminiThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, parent, prompt):
        super().__init__()
        self.parent = parent
        self.prompt = prompt

    def run(self):
        response = self.parent.call_gemini_api(self.prompt)
        # ensure signal emits a string
        self.finished.emit(str(response))


class ChatWindow(QDialog):
    def __init__(self, parent):
        super().__init__(mw)
        self.parent = parent
        self.debug = DebugTools("ChatWindow")
        self.collapsed = False
        self.thread = None
        self.setup_ui()
        self.debug.log("ChatWindow setup completed")
        self.load_initial_message()

    def setup_ui(self):
        # Make the chat a compact, modern right-side panel (VS Code-like)
        self.setWindowTitle("Gemini AI Tutor")

        # stay on top and behave like a tool window; some Qt builds may not have Qt.Tool
        flags = Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # size and position: narrow panel at the right side of the main window
        width = 360
        height = min(mw.height() - 100, 800)
        self.setFixedSize(width, height)

        # move to right edge of Anki main window with a small margin
        try:
            mw_geom = mw.geometry()
            x = mw_geom.x() + mw_geom.width() - width - 12
            y = mw_geom.y() + 30
            self.move(x, y)
        except Exception:
            # fallback: center on screen
            self.move(100, 100)

        # overall layout
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header (compact) with title, collapse and close
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(6)

        title = QLabel("🤖 Gemini AI Tutor")
        title.setStyleSheet("font-weight:600; font-size:13px; color:#222;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.collapse_btn = QPushButton("—")
        self.collapse_btn.setFixedSize(24, 22)
        self.collapse_btn.setToolTip("Thu nhỏ/hiện")
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.collapse_btn)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 22)
        close_btn.setToolTip("Đóng")
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)

        header_widget.setLayout(header_layout)
        header_widget.setStyleSheet("background:#ffffff; border-radius:8px;")
        layout.addWidget(header_widget)

        # WebView for chat (message area)
        self.webview = AnkiWebView()
        self.webview.setMinimumHeight(int(height * 0.65))
        self.webview.setStyleSheet("border-radius:8px; background:#fafafa;")
        self.init_chat_html()
        layout.addWidget(self.webview)

        # Input area: compact single-line input with send icon-like button
        input_container = QWidget()
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Nhập câu hỏi...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)

        self.send_btn = QPushButton("Gửi")
        self.send_btn.setFixedHeight(28)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        input_container.setLayout(input_layout)
        input_container.setStyleSheet("background:transparent;")
        layout.addWidget(input_container)

        self.setLayout(layout)

    def init_chat_html(self):
        """Initialize chat HTML"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                :root { --bg: #f7fafc; --bot: #ffffff; --user: #0b63ff; --muted: #666; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin: 0; padding: 12px; background: var(--bg); color: #222; }
                .chat-messages { height: 100%; overflow-y: auto; padding-right: 6px; }
                .message { margin: 8px 0; padding: 10px 14px; border-radius: 12px; max-width: 80%; box-shadow: 0 1px 3px rgba(0,0,0,0.06); word-wrap: break-word; }
                .user-message { background: var(--user); color: white; margin-left: auto; text-align: left; }
                .bot-message { background: var(--bot); color: #111; margin-right: auto; border: 1px solid rgba(0,0,0,0.04); }
                .meta { font-size: 11px; color: var(--muted); margin-top: 6px; }
            </style>
        </head>
        <body>
            <div id="chat-messages" class="chat-messages"></div>
        </body>
        </html>
        """
        self.webview.setHtml(html)

    def load_initial_message(self):
        """Load initial explanation"""
        if not self.parent.current_card:
            return

        field_text = self.parent.get_field_text(self.parent.current_card, self.parent.config["target_field"]) if self.parent.current_card else ""
        if field_text:
            prompt = f"Giải thích về: '{field_text}'"
            self.add_message("user", prompt)
            self.show_typing_indicator()

            # Call Gemini in background
            self.thread = GeminiThread(self.parent, prompt)
            self.thread.finished.connect(self.handle_gemini_response)
            self.thread.start()

    def add_message(self, sender, message):
        """Add message to chat"""
        safe_message = message.replace('`', '\\`').replace('${', '\\${')

        if sender == "user":
            html = f'<div class="message user-message"><strong>Bạn:</strong><br>{safe_message}</div>'
        else:
            html = f'<div class="message bot-message"><strong>AI:</strong><br>{safe_message}</div>'

        js = (
            "var messages = document.getElementById('chat-messages');"
            f"messages.innerHTML += `{html}`;"
            "messages.scrollTop = messages.scrollHeight;"
        )
        self.webview.eval(js)

    def show_typing_indicator(self):
        """Show typing indicator"""
        self.webview.eval("""
            var messages = document.getElementById('chat-messages');
            messages.innerHTML += '<div class="message bot-message"><em>AI đang trả lời...</em></div>';
            messages.scrollTop = messages.scrollHeight;
        """)

    def hide_typing_indicator(self):
        """Hide typing indicator"""
        self.webview.eval("""
            var messages = document.getElementById('chat-messages');
            var last = messages.lastElementChild;
            if (last && last.innerHTML.includes('đang trả lời')) {
                last.remove();
            }
        """)

    def send_message(self):
        """Send user message"""
        # support QLineEdit (new UI) and QTextEdit (legacy)
        if hasattr(self.message_input, 'text'):
            message = self.message_input.text().strip()
        else:
            message = self.message_input.toPlainText().strip()

        if not message:
            return

        self.add_message("user", message)
        # clear input appropriately
        if hasattr(self.message_input, 'clear'):
            self.message_input.clear()
        self.show_typing_indicator()

        self.thread = GeminiThread(self.parent, message)
        self.thread.finished.connect(self.handle_gemini_response)
        self.thread.start()

    def toggle_collapse(self):
        """Toggle collapse/expand of the chat body"""
        if self.collapsed:
            # expand
            self.webview.show()
            # restore size
            width = 360
            height = min(mw.height() - 100, 800)
            self.setFixedSize(width, height)
            self.message_input.show()
            self.send_btn.show()
            self.collapse_btn.setText("—")
            self.collapsed = False
        else:
            # collapse to header-only (small height)
            self.webview.hide()
            self.message_input.hide()
            self.send_btn.hide()
            self.setFixedHeight(60)
            self.collapse_btn.setText("▢")
            self.collapsed = True

    def handle_gemini_response(self, response):
        """Handle API response"""
        self.hide_typing_indicator()
        self.add_message("bot", str(response))