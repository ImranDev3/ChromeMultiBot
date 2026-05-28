# Chrome Commander Pro 🚀

Professional-grade Chrome multi-profile automation tool with KeyAuth licensing, proxy integration, anti-bot delays, and window management.

## ✨ Features

- **12+ Dynamic Profiles** — Checkbox UI with unlimited dynamic profile addition at runtime
- **KeyAuth Licensing** — Secure license key validation via KeyAuth API
- **Persistent Sessions** — Each profile uses its own `--user-data-dir` so Facebook, Gmail, etc. stay logged in
- **Per-Profile Proxy** — IP:Port:User:Pass with auto-auth Chrome extension generation
- **Custom User-Agent** — Assign a unique User-Agent per profile
- **Mute Audio** — Toggle `--mute-audio` flag per profile
- **Custom Extension Loading** — `--load-extension` per profile
- **Anti-Bot Delay** — Random 2-5 second delays between profile launches
- **Window Tiling** — Auto-arrange Chrome windows in a grid
- **Profile Search & Tags** — Filter profiles by name or color-coded tags (Trading, Social, Work...)
- **Live Log Console** — Real-time launch log with timestamps and status emojis
- **Progress Bar** — Visual launch progress
- **Force Kill** — One-click `taskkill /F /IM chrome.exe`

## 🖥️ Screens

### Login Window
Dark-themed license activation with:
- License key entry field
- "Remember License Key" (encrypted local storage)
- KeyAuth API validation
- Clean error messaging

### Dashboard (Chrome Commander Pro)
Full-featured control panel with:
- Search bar + tag filter dropdown
- Scrollable profile list with expandable Advanced Settings
- "+ Add Profile" button for runtime profile creation
- 5 URL input fields
- Human-Like Launch toggle with configurable delay range
- Launch / Tile / Kill action buttons
- Real-time progress bar and log console

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python run.py
```

On first run the app auto-installs `customtkinter` and `requests` if missing.

## 📁 Project Structure

```
ChromeMultiBot/
├── run.py                                      # Entry point
├── requirements.txt                            # Dependencies
├── chrome_profile_launcher/
│   ├── __init__.py
│   ├── app.py                                  # Login UI + Main Dashboard
│   ├── config.py                               # Config persistence (JSON)
│   ├── keyauth.py                              # KeyAuth API wrapper
│   └── launcher.py                             # Chrome launch + proxy ext + tiling
└── README.md
```

## 🔧 How It Works

### Profile Launch Logic
- **Profile 1** uses Chrome profile directory `Default`
- **Profile 2+** use `Profile 1`, `Profile 2`, etc.
- Each profile stores cookies/sessions in `~/.chromemultibot/chrome_data/`

### Proxy Authentication
When a proxy with username/password is configured, the app generates a temporary Chrome extension with `chrome.webRequest.onAuthRequired` listener that auto-fills credentials.

### User-Agent Spoofing
Custom User-Agents are injected via the `--user-agent` Chrome flag.

## 🔐 License System

This application uses **KeyAuth** for license validation:
- **Application Name:** ChromeMultiBot
- **Version:** 1.0

Contact **ImranDev3** to obtain a valid license key.

## 📋 Requirements

- Windows OS
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 3.7+
- Internet connection (for KeyAuth validation)

---

**Developed by [ImranDev3](https://github.com/ImranDev3)**
