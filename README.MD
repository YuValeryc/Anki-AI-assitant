# Gemini Chat for Anki

Anki Add-on that integrates an interactive **AI chat assistant** directly inside Anki.  
It allows users to **send prompts** related to cards, decks, or custom queries and get **instant responses** from a large language model (e.g., Gemini API).  
Supports **per-deck prompt customization**, **multi-note-type handling**, and **detailed logging** for debugging.

---

## Features

- Embedded chat window inside the Anki Reviewer  
- Per-deck prompt configuration  
- Supports multiple note types within the same parent deck  
- Custom prompts input field — unlocked when "Custom Prompt" is selected  
- Built-in logging to console and optionally to file  
- Deck-wide notetype scanner (quickly check all notetypes in a deck)  
- Safe handling for notes missing specific fields  

---

## How It Works

1. When reviewing a card, a **chat button** appears on the screen.  
2. Clicking it opens a chat window with Gemini (or your preferred model).  
3. The addon uses the **deck configuration** to determine which prompt template to send.  
4. If the selected prompt is `"Custom Prompt"`, you can manually enter any text before sending.  

---

## Installation

You can install this add-on directly from **AnkiWeb**:

**Add-on Code:** `.....`  
**AnkiWeb Page:** [https://ankiweb.net/shared/info/..](https://ankiweb.net/shared/info/...)

Alternatively, you can install it manually by cloning or downloading this repository into your Anki add-ons directory.
After installation:
1. Restart Anki.  
2. Go to **Tools → Gemini Chat Config** to configure prompts, API keys, and other options.  

---

# Usage

1. Open the Anki **Reviewer**.  
2. You will see a **chat button** appear in the bottom-right corner of the screen.  
3. Click it to open the chat window.  
4. Choose a **prompt template** (e.g., “Explain grammar”, “Translate sentence”), or select **Custom Prompt** to type your own question.  
5. The add-on will automatically collect the card’s field data and send it to the model.  
6. The response will appear inside the chat window.

You can customize:
- **Deck prompts:** Each deck can have its own predefined or custom prompt.  
- **Model integration:** You can configure Gemini or any compatible API endpoint.  

## Note

- If your **parent deck** contains multiple note types, the add-on will only process notes whose fields match the configured notetype.  
- When using **Custom Prompt**, make sure the input field below the dropdown is **enabled** before sending.  
- Missing fields in cards are safely skipped to prevent errors.  
- For better debugging, enable **logging to file** in the configuration menu.  

If you encounter issues:
- Check the Anki console (Ctrl + `) for log output.  
- Verify that your API key and endpoint are correctly configured.  
- Restart Anki after changing configuration settings.  
