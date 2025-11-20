# 🤖 Gemini Chat for Anki

[![AnkiWeb](https://img.shields.io/badge/AnkiWeb-1725302966-blue)](https://ankiweb.net/shared/info/1725302966)
[![Anki](https://img.shields.io/badge/Anki-2.1+-brightgreen.svg)](https://apps.ankiweb.net/)

An intelligent AI chat assistant seamlessly integrated into your Anki study sessions. Get instant help with grammar explanations, translations, examples, and custom questions while reviewing your cards.

---

## 📖 Overview

**Gemini Chat for Anki** brings AI-powered assistance directly into your Anki reviewer. Whether you need grammar explanations, translations, or want to ask custom questions about your cards, this add-on makes your study sessions more interactive and productive using Google's Gemini API.

## ✨ Key Features

- 💬 **Embedded Chat Window** – Built directly into the Anki reviewer
- 🎯 **Context-Aware Responses** – AI automatically receives your card content
- ⚙️ **Per-Deck Configuration** – Different prompts for different decks
- 📝 **Multiple Note Type Support** – Works with various card templates
- ✏️ **Custom Prompts** – Ask any question about your cards
- 🔧 **Flexible API Support** – Compatible with Gemini and other AI models

---

## 🚀 Installation

### Quick Install from AnkiWeb

1. Open Anki
2. Go to **Tools → Add-ons → Get Add-ons...**
3. Enter code: `1725302966`
4. Click **OK** and restart Anki

**AnkiWeb:** [https://ankiweb.net/shared/info/1725302966](https://ankiweb.net/shared/info/1725302966)

### Manual Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/YuValeryc/Anki-AI-assitant.git
   ```

2. Copy to your Anki add-ons directory:
   - **Windows:** `%APPDATA%\Anki2\addons21\`
   - **macOS:** `~/Library/Application Support/Anki2/addons21/`
   - **Linux:** `~/.local/share/Anki2/addons21/`

3. Restart Anki

---

## ⚙️ Initial Configuration

### Step 1: Get Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the generated API key

### Step 2: Configure the Add-on

1. In Anki, go to **Tools → Gemini Chat Config**
2. In the configuration window:
   - Paste your **API Key** in the API Key field
   - Leave the **API Endpoint** as default (or customize if needed)
   - Click **Save**

---

## 🎯 Enabling Chatbot for a Deck

Follow these steps to configure the chatbot for a specific deck:

### Step 1: Open Deck Configuration

1. Go to **Tools → Gemini Chat Config**
2. In the configuration window, you'll see:
   - **Deck Selector** dropdown at the top
   - **Note Type Selector** below it
   - **Prompt Configuration** area

### Step 2: Select Your Deck

1. Click the **Deck Selector** dropdown
2. Choose the deck you want to enable the chatbot for
3. The add-on will scan for available note types in that deck

### Step 3: Choose Note Type

1. Click the **Note Type Selector** dropdown
2. Select the note type you're using for your cards
3. The add-on will display available fields for that note type

### Step 4: Configure Prompts

You have two options:

#### Option A: Use Pre-defined Prompts

1. In the **Prompt Templates** section, you'll see options like:
   - **Explain Grammar**
   - **Translate Sentence**
   - **Provide Examples**
   - **Simplify Explanation**
2. Select the prompt that matches your study needs
3. Click **Save**

#### Option B: Create Custom Prompt Template

1. Select **Custom Prompt** from the dropdown
2. In the text area, write your custom prompt template
3. Use field placeholders like `{Front}`, `{Back}`, `{Word}`, etc.
4. Example custom prompt:
   ```
   Explain the grammar structure of: {Sentence}
   Also provide 2 example sentences using the same pattern.
   ```
5. Click **Save**

### Step 5: Test the Configuration

1. Open your deck and start reviewing
2. You should see a **Chat** button in the bottom-right corner
3. Click it to test the chatbot

---

## 📝 Using Custom Prompts During Review

There are two ways to use custom prompts:

### Method 1: Quick Custom Question (Recommended)

1. While reviewing a card, click the **Chat** button
2. In the chat window, select **Custom Prompt** from the dropdown
3. The input field below will become **enabled**
4. Type your question (the card fields are automatically included)
5. Examples:
   - "Can you give me 5 more example sentences?"
   - "What's the difference between this word and its synonym?"
   - "Explain this grammar point in simple terms"
6. Click **Send**

### Method 2: Pre-configured Custom Prompts

1. Configure custom prompt templates in **Tools → Gemini Chat Config**
2. Save multiple prompt templates for different purposes
3. During review, select your saved template from the dropdown
4. Click **Send**

---

## 💡 Usage Examples

### Example 1: Language Learning Deck

**Deck:** Japanese Vocabulary  
**Note Type:** Basic  
**Fields:** Word, Reading, Meaning, Example

**Configuration:**
- **Deck:** Japanese Vocabulary
- **Note Type:** Basic
- **Custom Prompt Template:**
  ```
  For the word "{Word}" ({Reading}):
  1. Provide 3 example sentences with English translation
  2. List common collocations
  3. Mention any similar words and their differences
  ```

### Example 2: Medical School Deck

**Deck:** Anatomy  
**Note Type:** Cloze  
**Fields:** Text, Extra

**Configuration:**
- **Deck:** Anatomy
- **Note Type:** Cloze
- **Custom Prompt Template:**
  ```
  About this medical concept: {Text}
  
  Please explain:
  - Clinical significance
  - Common exam questions
  - Memory techniques to remember this
  ```

### Example 3: On-the-Fly Questions

While reviewing any card:
1. Click **Chat** button
2. Select **Custom Prompt**
3. Type specific questions like:
   - "What are common mistakes with this concept?"
   - "Can you create a mnemonic to remember this?"
   - "Give me a real-world application example"

---

## 🔧 Advanced Configuration

### Multiple Note Types in One Deck

If your deck contains multiple note types:

1. Open **Tools → Gemini Chat Config**
2. Select your deck
3. Configure each note type separately:
   - Set up prompts for Note Type 1
   - Click **Save**
   - Select Note Type 2 from dropdown
   - Set up prompts for Note Type 2
   - Click **Save**
4. The add-on will automatically use the correct prompt based on the card's note type

### Custom API Endpoints

To use a different AI model:

1. Go to **Tools → Gemini Chat Config**
2. Change the **API Endpoint** field
3. Adjust the API Key accordingly
4. Click **Save**

### Field Mapping

The add-on automatically detects your card fields. You can use them in custom prompts:

- Use curly braces: `{FieldName}`
- Common field names: `{Front}`, `{Back}`, `{Word}`, `{Sentence}`, `{Extra}`
- If a field is missing, it's safely skipped

---

## 🛠️ Troubleshooting

### Chat Button Not Appearing

- ✅ Ensure add-on is enabled: **Tools → Add-ons**
- ✅ Restart Anki after installation
- ✅ Make sure you're in the reviewer (not deck browser)

### No Response from AI

- ✅ Check API key in **Tools → Gemini Chat Config**
- ✅ Verify internet connection
- ✅ Check API rate limits (Gemini has daily limits)
- ✅ Review console logs: Press `Ctrl + Shift + ` ` (Windows) or `Cmd + Shift + ` ` (macOS)

### Incorrect or Empty Fields

- ✅ Open configuration and verify note type selection
- ✅ Check that field names match exactly (case-sensitive)
- ✅ Ensure the card has content in those fields

### Custom Prompt Input Disabled

- ✅ Make sure you selected **"Custom Prompt"** from the dropdown
- ✅ The input field only activates when Custom Prompt is selected
- ✅ Try clicking the dropdown again to refresh

### Configuration Not Saving

- ✅ Click **Save** button after changes
- ✅ Restart Anki
- ✅ Check file permissions in add-on directory

---

## 📊 Debug Logging

For detailed troubleshooting:

1. Go to **Tools → Gemini Chat Config**
2. Enable **Log to Console** and/or **Log to File**
3. Reproduce the issue
4. Check logs:
   - **Console:** `Ctrl + Shift + ` ` (Windows/Linux) or `Cmd + Shift + ` ` (macOS)
   - **Log File:** Located in the add-on directory

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

- 🐛 Report bugs via [GitHub Issues](https://github.com/YuValeryc/Anki-AI-assitant/issues)
- 💡 Suggest new features
- 🔧 Submit pull requests
- 📚 Improve documentation

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🙏 Acknowledgments

- Built for [Anki](https://apps.ankiweb.net/) – the powerful spaced repetition system
- Powered by [Google Gemini API](https://ai.google.dev/)
- Made with ❤️ for the Anki learning community

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/YuValeryc/Anki-AI-assitant/issues)
- **AnkiWeb:** [Add-on Page](https://ankiweb.net/shared/info/1698042138)

**Happy Learning! 🎓**
