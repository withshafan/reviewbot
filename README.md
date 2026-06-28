<div align="center">
  <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" alt="Logo" width="80" height="80">
  <h1 align="center">🤖 ReviewBot</h1>
  
  <p align="center">
    <strong>AI-Powered Pull Request Reviewer built with Google Gemini & FastAPI</strong>
  </p>

  <p align="center">
    <a href="https://github.com/apps/reviewbot-dev-withshafan">
      <img src="https://img.shields.io/badge/Install-GitHub%20App-7A63FF?style=for-the-badge&logo=github&logoColor=white" alt="Install GitHub App" />
    </a>
    <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
    </a>
    <a href="https://ai.google.dev/">
      <img src="https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Google Gemini" />
    </a>
    <br/>
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
  </p>
</div>

---

## 📖 Table of Contents
- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [The Dashboard](#-the-dashboard)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 About the Project

**ReviewBot** is an intelligent GitHub App designed to automate the pull request review process. By seamlessly combining **static code analysis** (flake8) with **Google's powerful Gemini AI**, ReviewBot provides developers with real-time, context-aware, and actionable feedback directly inside their PRs. 

Gone are the days of missing obvious bugs or formatting issues. ReviewBot catches them instantly, allowing your human reviewers to focus on architectural decisions and business logic.

---

## ✨ Key Features

* 🧠 **AI-Powered Insights:** Uses Google's Gemini LLM to understand code context, detect logical bugs, and suggest improvements.
* ⚡ **Real-Time Inline Comments:** Automatically leaves line-specific comments on the PR diff, exactly where the issue occurs.
* 🛡️ **Static Analysis Pre-Filtering:** Runs `flake8` to catch syntax errors and PEP8 violations *before* asking the AI, saving tokens and time.
* 🎛️ **Highly Configurable:** Control severity thresholds, specify focus areas for the AI, and ignore specific files via a `.reviewbot.yaml` file in your repository.
* 📊 **Unified Single-Page Dashboard:** A gorgeous, dark-themed dashboard to monitor your app's health, review history, and API documentation.
* 🔒 **Secure Authentication:** Implements industry-standard GitHub App JWT authentication and webhook payload verification.

---

## 💻 The Dashboard

ReviewBot comes with a fully integrated, beautiful **Single-Page Application (SPA) Dashboard** built right into the FastAPI server. 

Navigate to the root URL (`/`) to access:
- **🏠 Overview:** Live statistics and an explanation of how the bot works.
- **📖 API Docs:** Fully interactive embedded Swagger UI and ReDoc.
- **📊 Dashboard:** A history of recent reviews and an interactive chart (via Chart.js).
- **💚 Health Check:** Real-time status indicators for your Database, API keys, and Server.
- **🎬 Interactive Demo:** A self-contained simulation showing exactly how the AI analyzes code.

---

## ⚙️ How It Works

1. **Push Code:** A developer opens or synchronizes a Pull Request on GitHub.
2. **Webhook Triggered:** GitHub sends a payload to the ReviewBot `/webhook` endpoint.
3. **Diff Analysis:** ReviewBot fetches the PR diff and parses out exactly which files and lines changed.
4. **Static Linting:** Changes are passed through `flake8`.
5. **AI Evaluation:** The code, diff context, and linting results are sent to Gemini AI for a comprehensive review.
6. **Feedback Posted:** ReviewBot posts the compiled feedback back to GitHub as an official Pull Request Review!

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance async Python framework. |
| **AI Engine** | [Google Gemini](https://ai.google.dev/) | State-of-the-art LLM for code comprehension. |
| **Database** | [SQLite](https://www.sqlite.org/index.html) / [SQLAlchemy](https://www.sqlalchemy.org/) | Stores review history and statistics. |
| **GitHub Integration** | [PyJWT](https://pyjwt.readthedocs.io/) & [httpx](https://www.python-httpx.org/) | Handles GitHub App authentication and API calls. |
| **Frontend UI** | HTML5, CSS3, Vanilla JS | GitHub-inspired dark theme SPA dashboard. |

---

## 🏁 Getting Started

### Prerequisites
* Python 3.10 or higher
* A registered GitHub App
* A Google Gemini API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/withshafan/reviewbot_project.git
   cd reviewbot_project
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Copy the example environment file and fill in your details:
   ```bash
   cp .env.example .env
   ```
   *Required variables include your GitHub App ID, Webhook Secret, Private Key, and Gemini API Key.*

5. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```
   *Your beautifully crafted dashboard is now live at `http://127.0.0.1:8000`!*

---

## 🎛️ Configuration

ReviewBot can be customized on a per-repository basis. You can copy the included `.reviewbot.yaml.example` to `.reviewbot.yaml` in the root of your target repository and customize it:

```yaml
# List of files or directories to ignore during code review
ignore_patterns:
  - "*.md"
  - "docs/"
  - "tests/"
  - "venv/"

# Custom instructions for the AI reviewer
custom_instructions: "Please ensure all Python code follows PEP 8 style guidelines. Focus on readability and maintainability. Point out any potential security issues or performance bottlenecks."

# Review strictness level: 'lax', 'normal', 'strict'
strictness: "normal"

# Max suggestions to provide
max_suggestions: 5
```

---

## 🚑 Troubleshooting

### Why does the Database show "Disconnected" in the Health Tab?

If you just launched the dashboard for the very first time, the Health tab might show **"Database: ❌ Disconnected"**. 

**Why?**
The health check queries the `review_history` table. Since you haven't received a webhook yet, the table is entirely empty.

**✅ The Quick Fix:**
You can manually initialize the database by running the built-in test script:
```bash
python test_post_review.py
```
*(This triggers the database initialization logic. Refresh your dashboard, and it will proudly display **✅ Connected**!)*

---

## 🤝 Contributing

Contributions make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<div align="center">
  Made with ❤️ by <a href="https://github.com/withshafan">withshafan</a>
</div>
