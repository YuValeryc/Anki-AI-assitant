# languages.py

TRANSLATIONS = {
    "vi": {
        # Config Dialog
        "menu_config": "Cấu hình ChatBot",
        "menu_deck_config": "Cài đặt theo Deck",
        "menu_test_api": "Test API Key",
        "menu_debug": "Debug Info",
        "config_title": "Cấu hình Gemini ChatBot",
        "api_key_label": "🔑 Gemini API Key:",
        "language_label": "🌐 Ngôn ngữ / Language:",
        "enable_chatbot": "Bật ChatBot",
        "max_tokens_label": "📊 Giới hạn Tokens:",
        "default_prompt_label": "💡 Prompt mặc định (fallback):",
        "custom_prompt_group": "🧠 Quản lý Prompt Tùy Chỉnh",
        "key_label": "🔑 Key:",
        "prompt_label": "💬 Prompt:",
        "btn_add_update": "➕ Thêm / Cập nhật",
        "btn_delete": "🗑️ Xóa",
        "btn_cancel": "Huỷ",
        "btn_save": "Lưu",
        "error_key_empty": "❌ Key không được để trống.",
        "error_key_space": "❌ Key không được chứa khoảng trắng.",
        "error_prompt_empty": "❌ Prompt không được để trống.",
        "error_prompt_format": "❌ Prompt phải chứa {text} hoặc {field_content}.",
        "msg_prompt_saved": "✅ Prompt '{key}' đã được thêm hoặc cập nhật.",
        "error_no_selection": "❌ Chưa chọn prompt nào để xóa.",
        "msg_prompt_deleted": "🗑️ Đã xóa prompt '{key}'.",
        "error_prompt_not_found": "❌ Prompt không tồn tại trong cấu hình.",
        
        # Deck Config Dialog
        "deck_config_title": "Cài đặt theo Deck",
        "select_deck_label": "📚 Chọn Deck:",
        "deck_search_placeholder": "Nhập tên deck để tìm nhanh",
        "enable_deck_chatbot": "Bật ChatBot cho deck này",
        "target_field_label": "🎯 Trường mục tiêu:",
        "deck_prompt_label": "💡 Prompt cho deck:",
        "create_custom_prompt_label": "➕ Tự tạo prompt mới:",
        "custom_key_placeholder": "Nhập key (vd: synonyms)",
        "custom_prompt_placeholder": "Nhập prompt (phải có {text})",
        "btn_add_prompt": "Thêm prompt",
        "btn_check_notetype": "🔍 Kiểm tra Notetype Deck cha",
        "msg_deck_saved": "✅ Đã lưu cho deck: {deck_name}",
        "error_no_notetype": "❌ Không tìm thấy notetype trong deck hoặc subdeck.",
        "error_custom_prompt_empty": "❌ Vui lòng nhập prompt tùy chỉnh trước khi lưu.",

        # Chat Window
        "header": "Anki Chatbot",
        "placeholder": "Nhập tin nhắn...",
        "send": "Gửi",
        "typing": "Chatbot của yuu đang gõ...",
        "welcome": "Chào bạn, tôi là Anki ChatBot. Tôi có thể giúp gì cho bạn?",
        "you": "Bạn",
        "ai": "AI",
        
        # Gemini Chatbot
        "api_key_missing": "❌ Lỗi: Chưa cấu hình API Key",
        "rate_limit": "❌ Lỗi Gemini: Quá nhiều yêu cầu (rate limited). Hãy thử lại sau",
        "connection_error": "❌ Lỗi kết nối Gemini: {e}",
        "internal_error": "❌ Lỗi Gemini nội bộ: {e}",
        "no_active_card": "Không có card nào đang active!",
        "configure_api_key": "Vui lòng cấu hình API Key trong menu Tools → Gemini ChatBot → Cấu hình",
        "chatbot_disabled_deck": "Chưa bật chatbot cho bộ deck này.",
        "api_test_success": "✅ API Key hoạt động tốt!",
        "api_test_failed": "❌ Lỗi API Key: {result}",
        "config_saved": "Cấu hình đã được lưu!",
        "tooltip_prompt": "Hỏi Gemini về: {text}"
    },
    "en": {
        # Config Dialog
        "menu_config": "ChatBot Configuration",
        "menu_deck_config": "Deck Settings",
        "menu_test_api": "Test API Key",
        "menu_debug": "Debug Info",
        "config_title": "Gemini ChatBot Configuration",
        "api_key_label": "🔑 Gemini API Key:",
        "language_label": "🌐 Language / Ngôn ngữ:",
        "enable_chatbot": "Enable ChatBot",
        "max_tokens_label": "📊 Max Tokens:",
        "default_prompt_label": "💡 Default Prompt (fallback):",
        "custom_prompt_group": "🧠 Custom Prompt Management",
        "key_label": "🔑 Key:",
        "prompt_label": "💬 Prompt:",
        "btn_add_update": "➕ Add / Update",
        "btn_delete": "🗑️ Delete",
        "btn_cancel": "Cancel",
        "btn_save": "Save",
        "error_key_empty": "❌ Key cannot be empty.",
        "error_key_space": "❌ Key cannot contain spaces.",
        "error_prompt_empty": "❌ Prompt cannot be empty.",
        "error_prompt_format": "❌ Prompt must contain {text} or {field_content}.",
        "msg_prompt_saved": "✅ Prompt '{key}' added or updated.",
        "error_no_selection": "❌ No prompt selected to delete.",
        "msg_prompt_deleted": "🗑️ Deleted prompt '{key}'.",
        "error_prompt_not_found": "❌ Prompt not found in config.",

        # Deck Config Dialog
        "deck_config_title": "Deck Settings",
        "select_deck_label": "📚 Select Deck:",
        "deck_search_placeholder": "Type deck name to search",
        "enable_deck_chatbot": "Enable ChatBot for this deck",
        "target_field_label": "🎯 Target Field:",
        "deck_prompt_label": "💡 Deck Prompt:",
        "create_custom_prompt_label": "➕ Create Custom Prompt:",
        "custom_key_placeholder": "Enter key (e.g., synonyms)",
        "custom_prompt_placeholder": "Enter prompt (must have {text})",
        "btn_add_prompt": "Add Prompt",
        "btn_check_notetype": "🔍 Check Parent Deck Notetype",
        "msg_deck_saved": "✅ Saved for deck: {deck_name}",
        "error_no_notetype": "❌ No notetype found in deck or subdecks.",
        "error_custom_prompt_empty": "❌ Please enter a custom prompt before saving.",

        # Chat Window
        "header": "Anki Chatbot",
        "placeholder": "Type a message...",
        "send": "Send",
        "typing": "Yuu's chatbot is typing...",
        "welcome": "Hello, I'm Anki ChatBot. How can I help you?",
        "you": "You",
        "ai": "AI",

        # Gemini Chatbot
        "api_key_missing": "❌ Error: API Key not configured",
        "rate_limit": "❌ Gemini Error: Rate limited. Please try again later.",
        "connection_error": "❌ Gemini Connection Error: {e}",
        "internal_error": "❌ Gemini Internal Error: {e}",
        "no_active_card": "No active card!",
        "configure_api_key": "Please configure API Key in Tools → Gemini ChatBot → Configuration",
        "chatbot_disabled_deck": "Chatbot is not enabled for this deck.",
        "api_test_success": "✅ API Key is working!",
        "api_test_failed": "❌ API Key Error: {result}",
        "config_saved": "Configuration saved!",
        "tooltip_prompt": "Ask Gemini about: {text}"
    }
}

def get_text(lang, key, **kwargs):
    """Get translated text"""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["vi"])
    text = lang_dict.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text
