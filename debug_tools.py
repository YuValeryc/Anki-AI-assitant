# debug_tools.py
import os
import sys
from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *


class DebugTools:
    def __init__(self, addon_name="GeminiChatBot"):
        self.addon_name = addon_name
        self.log_file = os.path.join(os.path.dirname(__file__), "debug_log.txt")

    def log(self, message, show_popup=False):
        """Log message to file and optionally show popup"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        log_entry = f"[{timestamp}] {message}"

        print(f"🔧 {self.addon_name}: {log_entry}")

        # Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

        # if show_popup:
        #     showInfo(f"🔧 {self.addon_name}\n\n{message}")

    def debug_hook(self, hook_name, *args):
        """Debug hook calls"""
        self.log(f"HOOK: {hook_name} - Args: {len(args)}", False)

    def inspect_card(self, card):
        """Inspect card details for debugging"""
        if not card:
            return "Card: None"

        info = [
            f"Card ID: {card.id}",
            f"Deck ID: {card.did}",
            f"Note ID: {card.nid}",
            f"Fields: {list(card.note().keys())}",
            f"Front: {card.note().fields[0][:50]}..." if card.note().fields else "No fields"
        ]
        return "\n".join(info)

    def inspect_webview(self, webview):
        """Inspect webview state"""
        if not webview:
            return "WebView: None"
        return f"WebView: {type(webview).__name__} - URL: {webview.url().toString() if webview.url() else 'No URL'}"