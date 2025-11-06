from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from PyQt6.QtCore import Qt
from .debug_tools import DebugTools


# ======================================================================
# CONFIG DIALOG — GLOBAL SETTINGS
# ======================================================================
class ConfigDialog(QDialog):
    def __init__(self, config, parent):
        super().__init__(mw)
        self.config = config
        self.parent = parent
        self.debug = DebugTools("ConfigDialog")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Cấu hình Gemini ChatBot")
        self.setFixedSize(500, 350)

        layout = QVBoxLayout()

        # API Key
        layout.addWidget(QLabel("🔑 Gemini API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setText(self.config.get("api_key", ""))
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

        # Default prompt for all (fallback)
        layout.addWidget(QLabel("💡 Prompt mặc định (fallback):"))
        self.default_prompt = QComboBox()
        self.default_prompt.setEditable(True)

        self.default_prompt.addItem("Giải thích ngắn gọn về {field_content}", "default_simple")

        # load custom prompts
        for key, text in self.config.get("custom_prompts", {}).items():
            self.default_prompt.addItem(f"{key}: {text}", key)

        sel_key = self.config.get("selected_prompt", "default_simple")
        idx = self.default_prompt.findData(sel_key)
        if idx != -1:
            self.default_prompt.setCurrentIndex(idx)
        else:
            self.default_prompt.setEditText(sel_key)

        layout.addWidget(self.default_prompt)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()

        cancel_btn = QPushButton("Huỷ")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton("Lưu")
        save_btn.clicked.connect(self.accept)
        btns.addWidget(save_btn)

        layout.addLayout(btns)
        self.setLayout(layout)

    # Return updated config
    def get_config(self):
        return {
            "enabled": self.enabled.isChecked(),
            "api_key": self.api_key.text(),
            "max_tokens": self.max_tokens.value(),
            "selected_prompt": self.default_prompt.currentData() or self.default_prompt.currentText(),
            "custom_prompts": self.config.get("custom_prompts", {}),
            "deck_settings": self.config.get("deck_settings", {})
        }


# ======================================================================
# PER-DECK CONFIG
# ======================================================================
class DeckConfigDialog(QDialog):
    def __init__(self, config, parent):
        super().__init__(mw)
        self.config = config
        self.parent = parent
        self.debug = DebugTools("DeckConfigDialog")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Cài đặt theo Deck")
        self.setFixedSize(400, 450)

        layout = QVBoxLayout()

        # Deck selector
        layout.addWidget(QLabel("📚 Chọn Deck:"))
        self.deck_combo = QComboBox()

        decks = sorted(mw.col.decks.all(), key=lambda d: d["name"].lower())
        for deck in decks:
            self.deck_combo.addItem(deck["name"], deck["id"])

        self.deck_combo.currentIndexChanged.connect(self.load_deck_settings)
        layout.addWidget(self.deck_combo)

        # Enable deck
        self.deck_enabled = QCheckBox("Bật ChatBot cho deck này")
        layout.addWidget(self.deck_enabled)

        # Target field per deck
        layout.addWidget(QLabel("🎯 Trường mục tiêu:"))
        self.deck_target_field = QComboBox()
        self.deck_target_field.setEditable(True)
        layout.addWidget(self.deck_target_field)

        # Prompt selector per deck
        layout.addWidget(QLabel("💡 Prompt cho deck:"))
        self.deck_selected_prompt = QComboBox()
        self.deck_selected_prompt.setEditable(True)

        # Add default simple prompt key
        self.deck_selected_prompt.addItem(
            "Giải thích ngắn gọn về {field_content}",
            "default_simple"
        )

        # Add custom prompts by KEY
        for key, text in self.config.get("custom_prompts", {}).items():
            self.deck_selected_prompt.addItem(f"{key}: {text}", key)

        layout.addWidget(self.deck_selected_prompt)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Lưu")
        btn_save.clicked.connect(self.save_deck_settings)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

        # Load first deck
        self.load_deck_settings()

    # Get fields for deck
    def _get_fields_for_deck(self, deck_id):
        fields = []
        card_id = mw.col.db.scalar(f"SELECT id FROM cards WHERE did = {deck_id} LIMIT 1")
        if card_id:
            card = mw.col.get_card(card_id)
            note = card.note()
            model = note.model()
            fields = [fld["name"] for fld in model["flds"]]
        return fields

    # ==================================================================
    # Load settings
    # ==================================================================
    def load_deck_settings(self):
        deck_id = str(self.deck_combo.currentData())
        deck_settings = self.config.setdefault("deck_settings", {})

        settings = deck_settings.get(deck_id, {})

        # Enabled
        self.deck_enabled.setChecked(settings.get("enabled", True))

        # Fields
        fields = self._get_fields_for_deck(deck_id)
        self.deck_target_field.clear()

        if fields:
            self.deck_target_field.addItems(fields)
            saved_field = settings.get("target_field", fields[0])
            idx = self.deck_target_field.findText(saved_field)
            if idx != -1:
                self.deck_target_field.setCurrentIndex(idx)
            else:
                self.deck_target_field.setEditText(saved_field)
        else:
            self.deck_target_field.addItem("Không tìm thấy trường (deck rỗng)")
            self.deck_target_field.setEnabled(False)

        # Prompt KEY
        saved_key = settings.get("selected_prompt", "default_simple")
        idx = self.deck_selected_prompt.findData(saved_key)

        if idx != -1:
            self.deck_selected_prompt.setCurrentIndex(idx)
        else:
            self.deck_selected_prompt.setEditText(saved_key)

        self.debug.log(f"[LOAD] Deck {deck_id} settings: {settings}")

    # ==================================================================
    # Save settings
    # ==================================================================
    def save_deck_settings(self):
        deck_id = str(self.deck_combo.currentData())

        self.config["deck_settings"][deck_id] = {
            "enabled": self.deck_enabled.isChecked(),
            "target_field": self.deck_target_field.currentText(),
            "selected_prompt": self.deck_selected_prompt.currentData()
                                or self.deck_selected_prompt.currentText()
        }

        self.parent.save_config()
        showInfo(f"✅ Đã lưu cài đặt cho deck: {self.deck_combo.currentText()}")
        self.debug.log(f"[SAVE] {deck_id} = {self.config['deck_settings'][deck_id]}")
