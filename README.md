# Chrome Commander Pro 🚀

Professional-grade Chrome multi-profile automation tool with KeyAuth licensing, proxy integration, anti-bot delays, and window management.

## ✨ Features

- **12+ Dynamic Profiles** — Checkbox UI with unlimited dynamic profile addition
- **Free Trial** — Use 3 profiles immediately, no license key required
- **KeyAuth Licensing** — Unlock all 12 profiles + advanced features
- **Persistent Sessions** — Each profile uses its own `--user-data-dir` for auto-login
- **Per-Profile Proxy** — IP:Port:User:Pass with auto-auth Chrome extension
- **Custom User-Agent** — Assign unique User-Agent per profile
- **Mute Audio** — Per-profile `--mute-audio` toggle
- **Extension Loading** — `--load-extension` per profile
- **Anti-Bot Delay** — Random 2-5s delays between profile launches
- **Window Tiling** — Auto-arrange Chrome windows in a grid
- **Profile Search & Tags** — Filter by name or color-coded tags
- **Live Log Console** — Real-time launch log with timestamps
- **Force Kill** — One-click `taskkill /F /IM chrome.exe`

## 🆓 Free vs Licensed

| Feature | Free Trial | Licensed |
|---------|-----------|----------|
| Profile 1-3 | ✅ | ✅ |
| Profile 4+ | ❌ Locked | ✅ |
| Proxy per profile | ❌ | ✅ |
| Custom User-Agent | ❌ | ✅ |
| Mute Audio | ❌ | ✅ |
| Extension Loading | ❌ | ✅ |
| Dynamic Add Profile | ❌ | ✅ |
| Tag profiles | ✅ | ✅ |
| Human-Like Delay | ✅ | ✅ |
| Window Tiling | ✅ | ✅ |
| Force Close | ✅ | ✅ |

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python run.py
```

Auto-installs `customtkinter` and `requests` on first run.

## 📁 Project Structure

```
ChromeMultiBot/
├── run.py                                      # Entry point
├── requirements.txt                            # Dependencies
├── chrome_profile_launcher/
│   ├── __init__.py
│   ├── app.py                                  # Dashboard + License Dialog
│   ├── config.py                               # Config persistence
│   ├── keyauth.py                              # KeyAuth API wrapper
│   └── launcher.py                             # Chrome launch + tiling
└── README.md
```

## 🔧 How It Works

### Profile Launch
- **Profile 1** → Chrome `Default` directory
- **Profile 2+** → `Profile 1`, `Profile 2`, etc.
- Sessions persist in `~/.chromemultibot/chrome_data/`

### Proxy Auth
Generates a temporary Chrome extension with `webRequest.onAuthRequired` to auto-fill credentials.

### License Validation
Uses **KeyAuth** API. On first launch, 3 profiles are free. Click the License button to activate.

## 📋 Requirements

- Windows OS
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 3.7+
- Internet connection (KeyAuth validation)

---

**Developed by [ImranDev3](https://github.com/ImranDev3)**
