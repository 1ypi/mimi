<div align="center">

# 🤖 MIMI - AI Command-Line Assistant

### *Your Intelligent Voice-Activated System Controller*

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Gemini API](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)](https://github.com)

<p align="center">
  <img src="https://raw.githubusercontent.com/1ypi/mimi/main/images/demo.gif" alt="MIMI Demo" width="800"/>
</p>

**MIMI** is a powerful AI-powered assistant that bridges natural language and system commands. Control your computer, launch applications, and automate tasks using simple voice commands or text input.

[Features](#-features) • [Installation](#-installation) • [Get API Key](#-getting-your-gemini-api-key) • [Usage](#-usage) • [Examples](#-examples)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎤 **Voice Control**
- Wake word activation ("MIMI")
- Bilingual support (English/Spanish)
- Natural language processing
- Real-time speech recognition

### 🖥️ **System Control**
- Execute terminal commands
- Launch applications & games
- Keyboard automation
- Screenshot capture & analysis

</td>
<td width="50%">

### 🎮 **Game Launcher**
- Detects installed games from:
  - Steam
  - Epic Games
  - Rockstar Games
  - Ubisoft Connect
  - EA/Origin
  - GOG Galaxy

### 🧠 **Smart Context**
- System information awareness
- Process monitoring
- Directory indexing
- Error recovery with retry logic

</td>
</tr>
</table>

---

## 🚀 Installation

### Prerequisites

- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Gemini API Key** (See [Getting Your API Key](#-getting-your-gemini-api-key))
- **Microphone** (for voice commands)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/1ypi/mimi.git
   cd mimi
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run MIMI**
   ```bash
   python mimi.pyw
   ```

4. **Enter your Gemini API key** when prompted

### Requirements File

Install the `requirements.txt`:

`pip install -r requirements.txt`


```txt
google-generativeai>=0.3.0
pyautogui>=0.9.54
psutil>=5.9.0
SpeechRecognition>=3.10.0
PyAudio>=0.2.13
Pillow>=10.0.0
gTTS>=2.3.2
pygame>=2.5.0
```

> **Note:** On Linux, you may need to install PortAudio first:
> ```bash
> sudo apt-get install portaudio19-dev python3-pyaudio
> ```

---

## 🔑 Getting Your Gemini API Key

### Step-by-Step Tutorial

<details>
<summary><b>📖 Click to expand the complete guide</b></summary>

#### 1. **Access Google AI Studio**

Go to [Google AI Studio](https://aistudio.google.com/) and sign in with your Google account.

<p align="center">
  <img src="https://raw.githubusercontent.com/1ypi/mimi/main/images/step1.png" alt="AI Studio Login" width="700"/>
</p>

#### 2. **Accept Terms of Service**

On your first visit, you'll see a popup asking you to accept the Terms of Service. Click **"Continue"** or **"Accept"**.

#### 3. **Get API Key**

In the left sidebar, click on **"Get API key"** or click the key icon.

<p align="center">
  <img src="https://raw.githubusercontent.com/1ypi/mimi/main/images/step2.png" alt="Get API Key Button" width="700"/>
</p>

#### 4. **Create API Key**

Click on **"Create API key"** button. You'll have two options:

- **Create API key in new project** *(Recommended for beginners)*
- **Create API key in existing project** *(If you already have a Google Cloud project)*

<p align="center">
  <img src="https://raw.githubusercontent.com/1ypi/mimi/main/images/step3.png" alt="Create API Key" width="700"/>
</p>

#### 5. **Copy Your API Key**

⚠️ **IMPORTANT:** Your API key will be displayed only once. Copy it immediately and store it in a safe place!

The key will look something like this:
```
AIzaSyB1234567890abcdefghijklmnopqrstuv
```

<p align="center">
  <img src="https://raw.githubusercontent.com/1ypi/mimi/main/images/step4.png" alt="Copy API Key" width="700"/>
</p>

#### 6. **Security Best Practices**

- ✅ Never share your API key publicly
- ✅ Never commit it to GitHub
- ✅ Use environment variables in production
- ✅ Monitor your usage in AI Studio
- ✅ Set up API restrictions if needed

</details>

### 📊 API Pricing & Limits

MIMI uses **Gemini 2.5 Flash Lite**, which offers generous free tier limits:

| Model | Free Tier | Rate Limit |
|-------|-----------|------------|
| **Gemini 2.5 Flash** | 15 RPM (Requests/min) | 1 million tokens/day |
| **Gemini 2.5 Flash Lite** | 15 RPM | 1 million tokens/day |

> 💡 **Tip:** For most users, the free tier is more than sufficient for daily use!

For more details, visit the [Gemini Pricing Page](https://ai.google.dev/pricing).

---

## 💻 Usage

### Text Mode

Simply type your command in natural language:

```
You: Open Chrome and go to YouTube
MIMI: Working on it...
[Chrome launches and navigates to YouTube]
MIMI: Done, sir
```

### Voice Mode

1. Click **"Start Voice Mode"** button
2. Say **"MIMI"** followed by your command
3. Example: *"MIMI, open calculator"*
4. Say *"MIMI, exit"* to stop voice mode

### Screenshot Mode

Add `/screen` to your command to include a screenshot:

```
You: What's on my screen? /screen
MIMI: [Takes screenshot and analyzes it]
```

### Language Toggle

Click the **"ES"** / **"EN"** button to switch between English and Spanish.

---

## 📝 Examples

### System Commands

| Command | Result |
|---------|--------|
| "Show running processes" | Lists all running applications |
| "Open task manager" | Launches Task Manager |
| "What's my CPU usage?" | Shows system statistics |
| "List installed programs" | Displays all installed software |

### Application Control

| Command | Result |
|---------|--------|
| "Open Chrome" | Launches Google Chrome |
| "Start Notepad" | Opens Notepad |
| "Launch VS Code" | Opens Visual Studio Code |
| "Open File Explorer" | Opens File Explorer |

### Game Launching

| Command | Result |
|---------|--------|
| "Play GTA V" | Launches GTA V via Rockstar |
| "Open Fortnite" | Starts Fortnite via Epic Games |
| "Launch CS:GO" | Opens CS:GO via Steam |

### Keyboard Automation

| Command | Result |
|---------|--------|
| "Lock my screen" | Presses Win+L |
| "Take a screenshot" | Presses Win+Shift+S |
| "Open search" | Presses Win+S |

### Web Navigation

| Command | Result |
|---------|--------|
| "Go to YouTube" | Opens browser and navigates |
| "Search for Python tutorials" | Opens Google search |
| "Open GitHub" | Navigates to github.com |

---

## ⚙️ Configuration

### Settings Window

Access advanced settings by clicking the **⚙** button:

- 🎤 **Select microphone device**
- 🔊 **Configure audio output**
- 🔑 **Change API key**
- 🌐 **Switch language**

### Config File Location

MIMI stores your API key securely at:

- **Windows:** `C:\Users\YourName\.mimi\config.json`
- **Linux/Mac:** `~/.mimi/config.json`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           User Interface (Tkinter)       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  Voice  │  │  Text   │  │ Screen  │ │
│  │  Input  │  │  Input  │  │  Shot   │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
└───────┼───────────┼─────────────┼───────┘
        │           │             │
        └───────────┼─────────────┘
                    ↓
        ┌───────────────────────┐
        │   Gemini AI (2.5 Flash)|
        │   - Context Analysis  │
        │   - Command Generation│
        └───────────┬───────────┘
                    ↓
        ┌───────────────────────┐
        │   Execution Engine    │
        │  ┌─────────────────┐  │
        │  │  Terminal Cmds  │  │
        │  ├─────────────────┤  │
        │  │  Keyboard Auto  │  │
        │  ├─────────────────┤  │
        │  │  App Launcher   │  │
        │  └─────────────────┘  │
        └───────────────────────┘
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Areas for Contribution

- 🌍 Additional language support
- 🎨 UI/UX improvements
- 🐛 Bug fixes
- 📚 Documentation enhancements
- 🚀 Performance optimizations

---

## 🐛 Troubleshooting

<details>
<summary><b>Microphone not detected</b></summary>

1. Check if your microphone is properly connected
2. Install PyAudio: `pip install PyAudio`
3. On Linux: `sudo apt-get install portaudio19-dev`
4. Select your microphone in Settings (⚙ button)

</details>

<details>
<summary><b>API Key errors</b></summary>

1. Verify your API key is correct
2. Check you accepted the Terms of Service in AI Studio
3. Ensure you have available quota
4. Try regenerating your API key

</details>

<details>
<summary><b>Commands not executing</b></summary>

1. Check the console output for error messages
2. Verify you have necessary permissions
3. Try running MIMI as administrator (Windows)
4. Check if the command is supported on your OS

</details>

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini API** - For the powerful AI capabilities
- **OpenAI** - For inspiration in voice assistants
- **Python Community** - For the amazing libraries

---

## 📞 Support

- 💬 **Issues:** [GitHub Issues](https://github.com/1ypi/mimi/issues)
- 💻 **Discord:** 1ypi

---

<div align="center">

### ⭐ If you find MIMI useful, please consider giving it a star!

Made with ❤️ by [Your Name](https://github.com/1ypi)

[⬆ Back to Top](#-mimi---ai-command-line-assistant)

</div>
