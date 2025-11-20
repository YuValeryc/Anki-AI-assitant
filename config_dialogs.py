from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from PyQt6.QtCore import Qt
from .debug_tools import DebugTools
from .languages import get_text


# ======================================================================
# CONFIG DIALOG — GLOBAL SETTINGS
# ======================================================================
class ConfigDialog(QDialog):
    def __init__(self, config, parent):
        super().__init__(mw)
        self.config = config
        self.parent = parent
        self.debug = DebugTools("ConfigDialog")
        self.initUI()

    def initUI(self):
        lang = self.config.get("language", "vi")
        self.setWindowTitle(get_text(lang, "config_title"))
        self.setFixedSize(500, 650)
        
        layout = QVBoxLayout()

        # --- Language Selection ---
        layout.addWidget(QLabel(get_text(lang, "language_label")))
        self.language = QComboBox()
        self.language.addItem("Tiếng Việt", "vi")
        self.language.addItem("English", "en")
        # Set current language
        index = self.language.findData(lang)
        if index >= 0:
            self.language.setCurrentIndex(index)
        layout.addWidget(self.language)

        # --- API Key ---
        layout.addWidget(QLabel(get_text(lang, "api_key_label")))
        self.api_key = QLineEdit()
        self.api_key.setText(self.config.get("api_key", ""))
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key)

        # --- Enable Checkbox ---
        self.enabled = QCheckBox(get_text(lang, "enable_chatbot"))
        self.enabled.setChecked(self.config.get("enabled", True))
        layout.addWidget(self.enabled)

        # --- Max Tokens ---
        layout.addWidget(QLabel(get_text(lang, "max_tokens_label")))
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 2000)
        self.max_tokens.setValue(self.config.get("max_tokens", 500))
        layout.addWidget(self.max_tokens)

        # --- Default Prompt ---
        layout.addWidget(QLabel(get_text(lang, "default_prompt_label")))
        self.default_prompt = QComboBox()
        self.default_prompt.setEditable(True)
        
        # Add default options
        self.default_prompt.addItem("Giải thích ngắn gọn về {text}", "explain_simple")
        self.default_prompt.addItem("Từ đồng nghĩa/trái nghĩa của {text}", "synonyms_antonyms")
        
        # Add custom prompts from config
        custom_prompts = self.config.get("custom_prompts", {})
        for key, text in custom_prompts.items():
            self.default_prompt.addItem(f"{key}: {text}", key)
            
        # Set current selection
        current_prompt = self.config.get("selected_prompt", "explain_simple")
        idx = self.default_prompt.findData(current_prompt)
        if idx >= 0:
            self.default_prompt.setCurrentIndex(idx)
        else:
            self.default_prompt.setEditText(current_prompt)
            
        layout.addWidget(self.default_prompt)

        # --- Custom Prompts Management ---
        group_box = QGroupBox(get_text(lang, "custom_prompt_group"))
        group_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.prompt_key = QLineEdit()
        self.prompt_text = QLineEdit()
        form_layout.addRow(get_text(lang, "key_label"), self.prompt_key)
        form_layout.addRow(get_text(lang, "prompt_label"), self.prompt_text)
        group_layout.addLayout(form_layout)

        btn_add = QPushButton(get_text(lang, "btn_add_update"))
        btn_add.clicked.connect(self.add_or_update_prompt)
        group_layout.addWidget(btn_add)

        self.prompt_list = QListWidget()
        self.prompt_list.itemClicked.connect(self.load_prompt_to_fields)
        group_layout.addWidget(self.prompt_list)
        self.refresh_prompt_list()

        btn_del = QPushButton(get_text(lang, "btn_delete"))
        btn_del.clicked.connect(self.delete_prompt)
        group_layout.addWidget(btn_del)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        # --- Buttons ---
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        
        # Localize buttons
        btn_box.button(QDialogButtonBox.StandardButton.Save).setText(get_text(lang, "btn_save"))
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText(get_text(lang, "btn_cancel"))
        
        layout.addWidget(btn_box)
        self.setLayout(layout)

    # Return updated config
    def get_config(self):
        return {
            "enabled": self.enabled.isChecked(),
            "language": self.language.currentData(),
            "api_key": self.api_key.text(),
            "max_tokens": self.max_tokens.value(),
            "selected_prompt": self.default_prompt.currentData() or self.default_prompt.currentText(),
            "custom_prompts": self.config.get("custom_prompts", {}),
            "deck_settings": self.config.get("deck_settings", {})
        }

    def add_or_update_prompt(self):
        lang = self.config.get("language", "vi")
        key = self.prompt_key.text().strip()
        text = self.prompt_text.text().strip()

        if not key:
            showInfo(get_text(lang, "error_key_empty"))
            return
        if " " in key:
            showInfo(get_text(lang, "error_key_space"))
            return
        if not text:
            showInfo(get_text(lang, "error_prompt_empty"))
            return
        if "{text}" not in text and "{field_content}" not in text:
            showInfo(get_text(lang, "error_prompt_format"))
            return

        self.config.setdefault("custom_prompts", {})
        self.config["custom_prompts"][key] = text

        # Cập nhật lại danh sách
        self.refresh_prompt_list()
        self.prompt_key.clear()
        self.prompt_text.clear()
        showInfo(get_text(lang, "msg_prompt_saved", key=key))
    
    def delete_prompt(self):
        lang = self.config.get("language", "vi")
        selected = self.prompt_list.currentItem()
        if not selected:
            showInfo(get_text(lang, "error_no_selection"))
            return

        key = selected.text().split(":", 1)[0].strip()
        if key in self.config.get("custom_prompts", {}):
            del self.config["custom_prompts"][key]
            self.refresh_prompt_list()
            showInfo(get_text(lang, "msg_prompt_deleted", key=key))
        else:
            showInfo(get_text(lang, "error_prompt_not_found"))
    
    def load_prompt_to_fields(self, item):
        try:
            key, text = item.text().split(":", 1)
            self.prompt_key.setText(key.strip())
            self.prompt_text.setText(text.strip())
        except ValueError:
            pass
    
    def refresh_prompt_list(self):
        self.prompt_list.clear()
        custom_prompts = self.config.get("custom_prompts", {})
        for key, text in sorted(custom_prompts.items(), key=lambda x: x[0].lower()):
            self.prompt_list.addItem(f"{key}: {text}")



# ======================================================================
# PER-DECK CONFIG
# ======================================================================
class DeckConfigDialog(QDialog):
    def __init__(self, config, parent):
        super().__init__(mw)
        self.config = config
        self.parent = parent
        self.debug = DebugTools("DeckConfigDialog")
        self.all_decks = []
        self.setup_ui()

    # =========================================================
    # UI SETUP
    # =========================================================
    def setup_ui(self):
        lang = self.config.get("language", "vi")
        self.setWindowTitle(get_text(lang, "deck_config_title"))
        self.setFixedSize(420, 580)

        layout = QVBoxLayout()

        # Deck selector
        layout.addWidget(QLabel(get_text(lang, "select_deck_label")))
        self.deck_search = QLineEdit()
        self.deck_search.setPlaceholderText(get_text(lang, "deck_search_placeholder"))
        self.deck_search.textChanged.connect(self.filter_decks)
        layout.addWidget(self.deck_search)
        self.deck_combo = QComboBox()
        self.deck_combo.currentIndexChanged.connect(self.load_deck_settings)
        layout.addWidget(self.deck_combo)
        self.all_decks = sorted(mw.col.decks.all(), key=lambda d: d["name"].lower())
        self._populate_deck_combo(self.all_decks)

        # Enable checkbox
        self.deck_enabled = QCheckBox(get_text(lang, "enable_deck_chatbot"))
        layout.addWidget(self.deck_enabled)

        # Target field
        layout.addWidget(QLabel(get_text(lang, "target_field_label")))
        self.deck_target_field = QComboBox()
        self.deck_target_field.setEditable(True)
        layout.addWidget(self.deck_target_field)

        # Prompt selector
        layout.addWidget(QLabel(get_text(lang, "deck_prompt_label")))
        self.deck_selected_prompt = QComboBox()
        self.deck_selected_prompt.setEditable(True)
        self.deck_selected_prompt.addItem("Giải thích ngắn gọn về {text}", "default_simple")
        for key, text in self.config.get("custom_prompts", {}).items():
            self.deck_selected_prompt.addItem(f"{key}: {text}", key)
        layout.addWidget(self.deck_selected_prompt)
        self.deck_selected_prompt.currentIndexChanged.connect(self._on_prompt_changed)

        # Custom prompt section
        layout.addWidget(QLabel(get_text(lang, "create_custom_prompt_label")))
        self.custom_key = QLineEdit()
        self.custom_key.setPlaceholderText(get_text(lang, "custom_key_placeholder"))
        layout.addWidget(self.custom_key)
        self.custom_text = QLineEdit()
        self.custom_text.setPlaceholderText(get_text(lang, "custom_prompt_placeholder"))
        layout.addWidget(self.custom_text)
        self.btn_add_prompt = QPushButton(get_text(lang, "btn_add_prompt"))
        self.btn_add_prompt.clicked.connect(self.add_custom_prompt)
        layout.addWidget(self.btn_add_prompt)
        self._toggle_custom_ui(False)  

        # Button section
        btn_layout = QHBoxLayout()

        btn_save = QPushButton(get_text(lang, "btn_save"))
        btn_save.clicked.connect(self.save_deck_settings)
        btn_layout.addWidget(btn_save)

        btn_check_types = QPushButton(get_text(lang, "btn_check_notetype"))
        btn_check_types.clicked.connect(self.check_deck_notetypes)
        btn_layout.addWidget(btn_check_types)

        layout.addLayout(btn_layout)
        layout.addStretch()
        self.setLayout(layout)

        self.load_deck_settings()

    # =========================================================
    # UI HELPER FUNCTIONS
    # =========================================================
    def _toggle_custom_ui(self, enabled):
        self.custom_key.setEnabled(enabled)
        self.custom_text.setEnabled(enabled)
        self.btn_add_prompt.setEnabled(enabled)

    def _on_prompt_changed(self):
        data = self.deck_selected_prompt.currentData()
        self._toggle_custom_ui(data is None or data == "custom")

    def _populate_deck_combo(self, decks, selected_id=None):
        current_selection = selected_id
        if current_selection is None and self.deck_combo.count():
            current_selection = self.deck_combo.currentData()
        self.deck_combo.blockSignals(True)
        self.deck_combo.clear()
        for deck in decks:
            self.deck_combo.addItem(deck["name"], deck["id"])
        target_idx = -1
        if current_selection is not None:
            target_idx = self.deck_combo.findData(current_selection)
        if target_idx == -1 and self.deck_combo.count():
            target_idx = 0
        if target_idx != -1:
            self.deck_combo.setCurrentIndex(target_idx)
        self.deck_combo.blockSignals(False)

    def filter_decks(self, text):
        if not self.all_decks:
            return
        query = text.strip().lower()
        if not query:
            filtered = self.all_decks
        else:
            filtered = [d for d in self.all_decks if query in d["name"].lower()]
        current_id = self.deck_combo.currentData()
        valid_ids = {d["id"] for d in filtered}
        selected_id = current_id if current_id in valid_ids else None
        self._populate_deck_combo(filtered, selected_id)
        if self.deck_combo.count():
            self.load_deck_settings()


    # =========================================================
    # DATABASE UTILITIES
    # =========================================================
    def _get_subdecks(self, parent_id):
        subdecks = []
        all_decks = mw.col.decks.all()
        parent_name = mw.col.decks.get(parent_id)["name"]
        for d in all_decks:
            if d["name"].startswith(parent_name + "::"):
                subdecks.append(d)
        return subdecks

    def _get_model_id_for_deck(self, deck_id):
        mid = mw.col.db.scalar(
            f"SELECT n.mid FROM notes n JOIN cards c ON n.id=c.nid WHERE c.did={deck_id} LIMIT 1"
        )
        return mid

    def _get_fields_for_model(self, model_id):
        if not model_id:
            return []
        model = mw.col.models.get(model_id)
        if not model:
            return []
        return [fld["name"] for fld in model["flds"]]

    # =========================================================
    # LOAD SETTINGS
    # =========================================================
    def load_deck_settings(self):
        deck_id = str(self.deck_combo.currentData())
        deck_name = self.deck_combo.currentText()
        # self.debug.log(f"[LOAD] Loading settings for deck: {deck_name} (ID={deck_id})")

        deck_settings = self.config.setdefault("deck_settings", {})
        settings = deck_settings.get(deck_id, {})
        self.deck_enabled.setChecked(settings.get("enabled", True))

        model_id = self._get_model_id_for_deck(deck_id)
        if not model_id:
            for sub in self._get_subdecks(deck_id):
                model_id = self._get_model_id_for_deck(sub["id"])
                if model_id:
                    # self.debug.log(f"[LOAD] Dùng model từ subdeck: {sub['name']}")
                    break

        fields = self._get_fields_for_model(model_id)
        self.deck_target_field.clear()
        if fields:
            self.deck_target_field.setEnabled(True)
            self.deck_target_field.addItems(fields)
            saved_field = settings.get("target_field", fields[0])
            idx = self.deck_target_field.findText(saved_field)
            if idx != -1:
                self.deck_target_field.setCurrentIndex(idx)
            else:
                self.deck_target_field.setEditText(saved_field)
        else:
            self.deck_target_field.addItem("Không tìm thấy trường")
            self.deck_target_field.setEnabled(False)

        saved_key = settings.get("selected_prompt", "default_simple")
        idx = self.deck_selected_prompt.findData(saved_key)
        if idx != -1:
            self.deck_selected_prompt.setCurrentIndex(idx)
        else:
            self.deck_selected_prompt.setEditText(saved_key)

        # self.debug.log(f"[LOAD] Deck {deck_name} settings: {settings}")

    # =========================================================
    # ADD CUSTOM PROMPT
    # =========================================================
    def add_custom_prompt(self):
        lang = self.config.get("language", "vi")
        key = self.custom_key.text().strip()
        text = self.custom_text.text().strip()
        if not key:
            showInfo(get_text(lang, "error_key_empty"))
            return
        if " " in key:
            showInfo(get_text(lang, "error_key_space"))
            return
        if not text:
            showInfo(get_text(lang, "error_prompt_empty"))
            return
        if "{text}" not in text and "{field_content}" not in text:
            showInfo(get_text(lang, "error_prompt_format"))
            return

        self.config.setdefault("custom_prompts", {})
        self.config["custom_prompts"][key] = text
        self.parent.save_config()
        self.deck_selected_prompt.addItem(f"{key}: {text}", key)
        idx = self.deck_selected_prompt.findData(key)
        if idx != -1:
            self.deck_selected_prompt.setCurrentIndex(idx)
        self.custom_key.clear()
        self.custom_text.clear()
        showInfo(get_text(lang, "msg_prompt_saved", key=key))
        # self.debug.log(f"[ADD PROMPT] {key} = {text}")

    # =========================================================
    # SAVE SETTINGS
    # =========================================================
    def save_deck_settings(self):
        lang = self.config.get("language", "vi")
        deck_id = str(self.deck_combo.currentData())
        deck_name = self.deck_combo.currentText()

        # self.debug.log(f"[SAVE] Saving settings for deck: {deck_name} (ID={deck_id})")

        model_id = self._get_model_id_for_deck(deck_id)
        if not model_id:
            # self.debug.log("[SAVE] Không tìm thấy model trong deck chính, thử subdeck...")
            for sub in self._get_subdecks(deck_id):
                model_id = self._get_model_id_for_deck(sub["id"])
                if model_id:
                    # self.debug.log(f"[SAVE] Model lấy từ subdeck: {sub['name']} (MID={model_id})")
                    break

        if not model_id:
            showInfo(get_text(lang, "error_no_notetype"))
            # self.debug.log("[SAVE] ❌ Không tìm thấy notetype nào.")
            return

        selected_data = self.deck_selected_prompt.currentData()
        if selected_data == "custom":
            # Người dùng đang nhập custom prompt thủ công
            custom_prompt = self.custom_text.text().strip()
            if not custom_prompt:
                showInfo(get_text(lang, "error_custom_prompt_empty"))
                return
            if "{text}" not in custom_prompt and "{field_content}" not in custom_prompt:
                showInfo(get_text(lang, "error_prompt_format"))
                return

            # Tạo key tạm riêng cho deck này
            custom_key = f"deck_{deck_id}_custom"
            self.config.setdefault("custom_prompts", {})
            self.config["custom_prompts"][custom_key] = custom_prompt
            selected_prompt_key = custom_key
            self.parent.save_config()
            # self.debug.log(f"[SAVE] Tạo custom prompt riêng: {custom_key} = {custom_prompt}")
        else:
            selected_prompt_key = selected_data or self.deck_selected_prompt.currentText()

        self.config["deck_settings"][deck_id] = {
            "enabled": self.deck_enabled.isChecked(),
            "target_field": self.deck_target_field.currentText(),
            "selected_prompt": selected_prompt_key
        }


        same_model_subs = []
        different_model_subs = []
        for sub in self._get_subdecks(deck_id):
            sub_model_id = self._get_model_id_for_deck(sub["id"])
            if sub_model_id == model_id:
                same_model_subs.append(sub)
            elif sub_model_id:
                different_model_subs.append((sub, sub_model_id))

        for sub in same_model_subs:
            sid = str(sub["id"])
            self.config["deck_settings"][sid] = {
                "enabled": self.deck_enabled.isChecked(),
                "target_field": self.deck_target_field.currentText(),
                "selected_prompt": self.deck_selected_prompt.currentData()
                                    or self.deck_selected_prompt.currentText()
            }
            # self.debug.log(f"[SAVE] ✅ Áp dụng cho subdeck: {sub['name']} (ID={sub['id']})")

        # if different_model_subs:
        #     # self.debug.log(f"[SAVE] ⚠️ Bỏ qua {len(different_model_subs)} subdeck có notetype khác:")
        #     for sub, mid in different_model_subs:
        #         self.debug.log(f"    - {sub['name']} (ID={sub['id']}, MID={mid})")

        self.parent.save_config()
        msg = get_text(lang, "msg_deck_saved", deck_name=deck_name)
        if different_model_subs:
            msg += f"\n⚠️ Bỏ qua {len(different_model_subs)} subdeck có notetype khác."
        showInfo(msg)
        # self.debug.log(f"[SAVE DONE] {deck_name} – Model ID={model_id}")

    # =========================================================
    # CHECK NOTETYPE (SIMPLIFIED VERSION)
    # =========================================================
    def check_deck_notetypes(self):
        try:
            deck_id = self.deck_combo.currentData()
            deck_name = self.deck_combo.currentText()
            all_decks = [mw.col.decks.get(deck_id)] + self._get_subdecks(deck_id)

            mids = set()
            for d in all_decks:
                did = d["id"]
                mids.update(mw.col.db.list(
                    f"SELECT DISTINCT n.mid FROM notes n JOIN cards c ON n.id=c.nid WHERE c.did={did}"
                ))

            mids = {mid for mid in mids if mid is not None}
            if not mids:
                showInfo(f"❌ Không tìm thấy notetype nào trong '{deck_name}' hoặc subdeck.")
                # self.debug.log(f"[CHECK] Không tìm thấy notetype trong {deck_name}")
                return

            if len(mids) == 1:
                showInfo(f"✅ Deck '{deck_name}' và các subdeck cùng 1 notetype.")
                # self.debug.log(f"[CHECK] ✅ {deck_name} cùng notetype (MID={list(mids)[0]})")
            else:
                showInfo(f"⚠️ Deck '{deck_name}' và các subdeck có nhiều notetype khác nhau ({len(mids)} loại).")
                # self.debug.log(f"[CHECK] ⚠️ {deck_name} có {len(mids)} notetype khác nhau: {mids}")

        except Exception as e:
            # self.debug.log(f"[CHECK ERROR] {e}")
            showInfo(f"❌ Lỗi khi kiểm tra notetype: {e}")
        try:
            deck_id = self.deck_combo.currentData()
            deck_name = self.deck_combo.currentText()

            all_decks = [mw.col.decks.get(deck_id)] + self._get_subdecks(deck_id)
            found = {}
            # self.debug.log(f"[CHECK] Kiểm tra notetype của '{deck_name}' và các subdeck...")

            for d in all_decks:
                did = d["id"]
                name = d["name"]
                mids = mw.col.db.list(f"SELECT DISTINCT n.mid FROM notes n JOIN cards c ON n.id=c.nid WHERE c.did={did}")
                for mid in mids:
                    model = mw.col.models.get(mid)
                    if model:
                        found.setdefault(model["name"], []).append(name)

            if not found:
                showInfo(f"❌ Không tìm thấy note nào trong deck '{deck_name}' hoặc subdeck.")
                # self.debug.log("[CHECK] Không tìm thấy notetype nào.")
                return

            msg = f"📚 Notetype trong '{deck_name}' và các subdeck:\n\n"
            for model_name, decks in found.items():
                msg += f"• {model_name} ({len(decks)} deck):\n"
                for dname in decks:
                    msg += f"    - {dname}\n"
            showInfo(msg)

            # self.debug.log("[CHECK] Kết quả:")
            # for model_name, decks in found.items():
                # self.debug.log(f"   - {model_name}: {', '.join(decks)}")

        except Exception as e:
            # self.debug.log(f"[CHECK ERROR] {e}")
            showInfo(f"❌ Lỗi khi kiểm tra notetype: {e}")
