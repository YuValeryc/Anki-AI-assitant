from aqt import mw
from aqt.utils import showInfo

try:
    from .gemini_chatbot import GeminiChatBot

    # Khởi tạo addon
    gemini_bot = GeminiChatBot()
except Exception as e:
    showInfo(f"Lỗi khởi tạo Gemini ChatBot: {str(e)}")