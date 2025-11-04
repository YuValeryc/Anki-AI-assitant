from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .debug_tools import DebugTools


class ConfigDialog(QDialog):
    def __init__(self, config, parent):
        super().__init__(mw)
        self.config = config
        self.parent = parent
        self.debug = DebugTools("ConfigDialog")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Cấu hình Gemini ChatBot")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout()

        # API Key
        layout.addWidget(QLabel("🔑 Gemini API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setText(self.config.get("api_key", ""))
        self.api_key.setPlaceholderText("Nhập API Key từ Google AI Studio...")
        layout.addWidget(self.api_key)

        # Enable/Disable
        self.enabled = QCheckBox("Bật ChatBot")
        self.enabled.setChecked(self.config.get("enabled", True))
        layout.addWidget(self.enabled)

        # Max Tokens
        layout.addWidget(QLabel("📊 Giới hạn Tokens:"))
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 2000)
        self.max_tokens.setValue(self.config.get("max_tokens", 500))
        layout.addWidget(self.max_tokens)

        # Target Field
        layout.addWidget(QLabel("🎯 Trường mục tiêu:"))
        self.target_field = QComboBox()
        self.target_field.setEditable(True)
        self.target_field.setEditText(self.config.get("target_field", "Front"))
        layout.addWidget(self.target_field)

        # Buttons
        btn_layout = QHBoxLayout()

        test_btn = QPushButton("Test API")
        test_btn.clicked.connect(self.test_api)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Huỷ")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Lưu")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def test_api(self):
        """Test API key"""
        self.parent.config["api_key"] = self.api_key.text()
        self.parent.test_api_key()

    def get_config(self):
        """Get updated configuration"""
        return {
            "enabled": self.enabled.isChecked(),
            "api_key": self.api_key.text(),
            "max_tokens": self.max_tokens.value(),
            "target_field": self.target_field.currentText(),
            "selected_prompt": self.config.get("selected_prompt", ""),
            "custom_prompts": self.config.get("custom_prompts", {}),
            "deck_settings": self.config.get("deck_settings", {})
        }


class DeckConfigDialog(QDialog):
    def __init__(self, config, parent):
        super().__init__(mw)
        self.config = config
        self.parent = parent
        self.debug = DebugTools("DeckConfigDialog")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Cài đặt theo Deck")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Chọn Deck:"))
        self.deck_combo = QComboBox()
        # Lấy danh sách deck và sắp xếp theo bảng chữ cái (không phân biệt hoa thường)
        decks = sorted(mw.col.decks.all(), key=lambda d: (d.get("name") or "").lower())
        for deck in decks:
            self.deck_combo.addItem(deck["name"], deck["id"])
        layout.addWidget(self.deck_combo)

        self.deck_enabled = QCheckBox("Bật ChatBot cho deck này")
        layout.addWidget(self.deck_enabled)

        # Load button
        load_btn = QPushButton("Tải cài đặt deck")
        load_btn.clicked.connect(self.load_deck_settings)
        layout.addWidget(load_btn)

        # Save button
        save_btn = QPushButton("Lưu cài đặt deck")
        save_btn.clicked.connect(self.save_deck_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def load_deck_settings(self):
        """Load settings for selected deck"""
        # Safely obtain deck id: currentData may be None on some Qt builds
        data = self.deck_combo.currentData()
        if data is None:
            # try resolving by deck name
            deck_name = self.deck_combo.currentText()
            try:
                resolved_id = mw.col.decks.id(deck_name)
            except Exception:
                resolved_id = None
            deck_id = str(resolved_id) if resolved_id is not None else ""
        else:
            deck_id = str(data)

        # Ensure deck_settings dict exists
        deck_settings = self.config.get("deck_settings")
        if deck_settings is None:
            deck_settings = {}
            self.config["deck_settings"] = deck_settings

        settings = deck_settings.get(deck_id, {})
        self.deck_enabled.setChecked(settings.get("enabled", True))

    def save_deck_settings(self):
        """Save settings for selected deck"""
        data = self.deck_combo.currentData()
        if data is None:
            deck_name = self.deck_combo.currentText()
            try:
                resolved_id = mw.col.decks.id(deck_name)
            except Exception:
                resolved_id = None
            deck_id = str(resolved_id) if resolved_id is not None else ""
        else:
            deck_id = str(data)

        # Ensure deck_settings dict exists
        if self.config.get("deck_settings") is None:
            self.config["deck_settings"] = {}

        self.config["deck_settings"][deck_id] = {
            "enabled": self.deck_enabled.isChecked(),
            "selected_prompt": self.config.get("selected_prompt", ""),
            "target_field": self.config.get("target_field", "Front")
        }

        self.parent.save_config()
        showInfo(f"Đã lưu cài đặt cho deck: {self.deck_combo.currentText()}")