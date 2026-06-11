<div align="center">
  <h1>𒆙 VoidClaw</h1>
  <p><b>An Evolutionary, Cross-Platform Autonomous AI Agent</b></p>
  <p>Built for Windows, macOS, Linux, and Android (Termux)</p>
</div>

---

VoidClaw is a highly advanced, local-first AI agent framework. It acts as a continuous autonomous assistant that learns your preferences over time, interacts with your local filesystem, scrapes the web, and communicates with you via a premium Web UI, Telegram, or the Terminal.

## 🌟 Key Features

*   **🧠 Evolutionary Memory:** VoidClaw automatically deduces your preferences, workflows, and expertise, saving them to its permanent `user.md` memory vault to adapt its personality to you.
*   **🌐 Tri-Channel Interface:** Chat with the agent via a high-end Glassmorphism **Web UI**, remotely via **Telegram**, or directly in the **Terminal**. All channels are synced in real-time.
*   **🔌 Universal LLM Support:** Easily switch between top-tier models from **Google (Gemini), OpenAI, Claude (Anthropic), Ollama (Local), NVIDIA NIM, and OpenRouter**.
*   **🛠️ Robust Tool Arsenal:**
    *   **Python Sandbox:** Executes Python code in a secure local environment.
    *   **Local RAG Engine:** Semantically searches your workspace files using local TF-IDF (No vector database required).
    *   **Media Downloader & Converter:** Downloads YouTube videos/audio and converts formats using FFmpeg.
    *   **Web Scraper:** Bypasses paywalls to extract clean text from any URL.
    *   **Transcript Fetcher:** Extracts closed captions from YouTube links instantly.
    *   **Live Weather:** Real-time terminal-based weather fetching.
    *   **File Manager:** Reads, writes, lists, and deletes files securely within the `workspace/` sandbox.

## 🚀 Installation & Setup

VoidClaw is designed to be **100% portable**. You can clone it, put it on a USB drive, and run it anywhere.

### Prerequisites
*   Python 3.10+
*   Git

### Windows Setup
1. Clone the repository.
2. Double-click `windows\install.bat`.
3. Follow the beautiful **Configuration Wizard** to set your LLM Provider, Model, and API Keys.
4. Run `windows\run.bat` to launch the agent.

### macOS & Linux Setup
```bash
git clone <your-repo-url>
cd voidclaw
chmod +x linux/install.sh linux/run.sh
./linux/install.sh
# To start the agent:
./linux/run.sh
```

### Android (Termux) Setup
Turn your phone into an AI Command Center!
1. Install **Termux** from F-Droid.
2. Run the following commands:
```bash
pkg install git
git clone <your-repo-url>
cd voidclaw
chmod +x termux/install.sh termux/run.sh
./termux/install.sh
# To start the agent:
./termux/run.sh
```

## 🖥️ The Web Command Center

When you launch VoidClaw, a production-grade Waitress/Flask server starts, and your browser will automatically open the Web UI (`http://localhost:5000`).

*   **Deep Space Dark Mode:** A stunning UI with orange/amber accents.
*   **Real-Time Streaming:** Responses stream word-by-word via Server-Sent Events (SSE).
*   **Settings Modal:** Tweak the agent's creativity (Temperature) and System Prompt on the fly.
*   **Memory Vault:** Browse and instantly restore previous chat sessions from the sidebar.

## 🔐 Privacy & Security

*   Your API keys and Chat Histories are automatically ignored by Git (`.gitignore`).
*   The agent is sandbox-restricted to only modify files inside the `workspace/` directory.

---
*Created for the future of autonomous computing.*
