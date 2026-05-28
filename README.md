# Chrome Commander Pro 🚀

Professional Chrome multi-profile automation tool with **offline MD5-hash license validation** — no internet required.

## ✨ Features

- **Offline License System** — MD5 hash-based key verification, no API calls
- **12+ Dynamic Profiles** — Checkbox UI with runtime profile addition
- **5 URL Inputs** — Pre-filled defaults, open all as tabs per profile
- **Per-Profile Proxy** — Assign `IP:Port` to any profile
- **Custom Tags** — Color-coded tags (Trading, Social, Work...)
- **Anti-Bot Delay** — Random 2-5s delays between profile launches
- **Mute Audio** — Global `--mute-audio` toggle
- **Window Tiling** — Auto-arrange Chrome windows in a grid
- **Force Kill** — One-click `taskkill /F /IM chrome.exe`
- **Persistent Sessions** — Each profile uses its own `--user-data-dir`

## 🔐 License System (Offline)

No internet connection required. Keys are verified locally using MD5 hashes.

| Key | Status |
|-----|--------|
| `CHROME-PRO-ALPHA` | ✅ Full unlock |
| `CHROME-PRO-BETA` | ✅ Full unlock |
| `CHROME-PRO-GAMMA` | ✅ Full unlock |

Without a key: 3 profiles available (trial mode).  
With a valid key: all 12+ profiles + proxy support unlocked.

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python run.py
```

## 📁 Structure

```
ChromeMultiBot/
├── run.py                        # Entry point
├── requirements.txt
├── chrome_profile_launcher/
│   ├── __init__.py
│   ├── app.py                    # Activation window + Dashboard
│   ├── launcher.py               # Chrome launch + tiling + kill
│   └── license.py                # Offline MD5 hash verification
└── README.md
```

## 🔧 How It Works

- **Profile 1** → Chrome's `Default` directory
- **Profile 2+** → `Profile 1`, `Profile 2`, etc.
- Sessions stored in `~/.chromemultibot/chrome_data/`
- License stored in `~/.chromemultibot/license_config.json`
- Saved key is auto-verified on next launch

## 📋 Requirements

- Windows OS
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 3.7+

---

**Developed by [ImranDev3](https://github.com/ImranDev3)**
