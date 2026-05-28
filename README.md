# ChromeMultiBot 🚀

Professional Python desktop tool to launch multiple Chrome profiles with persistent sessions, proxy support, anti-bot delays, and window tiling.

## Features

- **12 Profile Manager** — Checkbox UI with Select All / Deselect All
- **Persistent Login** — Each profile uses its own `--user-data-dir` so logins persist
- **Proxy Integration** — Per-profile proxy with auto-auth via Chrome extension
- **Human-Like Launch** — Random 2-5s delays between profile launches
- **Window Tiling** — Auto-arrange Chrome windows in a grid
- **Profile Search & Tags** — Search by name/tag, color-coded tags (Trading, Social, Work...)
- **Log Console** — Real-time launch log with timestamps
- **Progress Bar** — Visual launch progress indicator
- **5 URL Inputs** — Pre-filled defaults, open all as tabs in each profile
- **License System** — Free trial (3 profiles) or full unlock with license key

## License System

- **Free Trial**: Use up to 3 profiles with all basic features
- **Full License**: Unlock all 12 profiles + Proxy integration
- Contact **ImranDev3** to get a license key
- Enter the key via the License button in the app

## Quick Start

```bash
python run.py
```

Auto-installs `customtkinter` on first run.

## Project Structure

```
ChromeMultiBot/
├── run.py                              # Entry point
├── keygen.py                           # License key generator (dev only, not in repo)
├── chrome_profile_launcher/
│   ├── __init__.py
│   ├── app.py                          # CustomTkinter UI
│   ├── config.py                       # JSON config persistence
│   ├── launcher.py                     # Chrome launch, proxy ext, tiling
│   └── license.py                      # License verification + trial limits
└── README.md
```

## Requirements

- Windows OS
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 3.7+

## Details

| Feature | Description |
|---|---|
| **Select All / Deselect All** | Buttons at the top of the profile list |
| **Search** | Filter profiles by name or tag |
| **Tags** | Color-coded labels, click "+" to add custom tags |
| **Proxy** | Click ⚙ on a profile, enable proxy, set IP:Port:User:Pass |
| **Human-Like Launch** | Toggle in settings, configurable delay range |
| **Tile Windows** | Arranges new Chrome windows in a grid after launch |
| **Force Close** | `taskkill /F /IM chrome.exe` — kills all Chrome processes |
| **Persistent Sessions** | Profiles stored at `~/.chromemultibot/chrome_data/Profile_N/` |

Configuration auto-saves to `~/.chromemultibot/config.json`.

---

**Developed by [ImranDev3](https://github.com/ImranDev3)**
