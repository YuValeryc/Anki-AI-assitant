import os
import sys

# 🎯 ENABLE DEBUG EARLY
os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '8080'

# Add addon directory to path
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

from aqt import mw
from aqt.utils import showInfo

try:
    from .gemini_chatbot import GeminiChatBot

    # Khởi tạo addon
    gemini_bot = GeminiChatBot()
except Exception as e:
    showInfo(f"Lỗi khởi tạo Gemini ChatBot: {str(e)}")