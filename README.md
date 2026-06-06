# WiFi Meter 🛜

A lightweight, always-on-top Windows desktop widget that monitors real-time network upload/download speeds and tracks cumulative data usage per session.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Real-time Speed** | Displays upload (↑) and download (↓) speeds updated every second |
| **Session Totals** | Tracks cumulative data transferred since the widget was launched |
| **System Tray** | Minimize to system tray; show/hide via tray icon |
| **Themes** | 4 built-in themes — Dark, Light, Neon, Cyberpunk |
| **Interface Selection** | Choose a specific Wi-Fi adapter or monitor all interfaces |
| **Lock Position** | Lock the widget in place to prevent accidental dragging |
| **Always On Top** | Toggle whether the widget stays above other windows |
| **Pause / Resume** | Pause monitoring with visual red indicator; green flash on resume |
| **Data Stats Window** | Detailed breakdown of session upload/download in a pop-up |
| **Stopwatch** | Built-in stopwatch utility (available in code, not yet in menu) |

---

## 📁 Project Structure

```
wifi meter/
├── main.py                # Application entry point & NetworkMonitor class
├── theme.py               # Theme configuration (colors, fonts, palettes)
├── verify_logic.py        # Diagnostic script for interface detection testing
├── requirements.txt       # Python dependencies
├── ui/
│   ├── __init__.py        # UI package initializer
│   ├── context_menu.py    # Right-click context menu manager
│   ├── data_stats.py      # Session data usage statistics window
│   ├── about_win.py       # About dialog (version & credits)
│   └── stopwatch.py       # Stopwatch utility window
└── *.spec                 # PyInstaller build specifications
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (with tkinter — included in standard Windows Python installs)
- **Windows OS** (uses Windows-specific features like system tray)

### Installation

1. **Clone or download** this project:
   ```bash
   git clone <repository-url>
   cd "wifi meter"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the widget**:
   ```bash
   python main.py
   ```

### Building an Executable

To create a standalone `.exe` using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "WiFi Meter" main.py
```

The executable will be created in the `dist/` folder.

> **Note**: The existing `.spec` files request `uac_admin=True` (administrator privileges). This is **not required** for network monitoring via `psutil` and should be removed unless you have a specific reason for elevated permissions.

---

## 🎨 Themes

Right-click the widget → **Theme** to switch between:

| Theme | Background | Accent Colors |
|---|---|---|
| **Dark** (default) | `#2b2b2b` | Red / Green / Blue |
| **Light** | `#ffffff` | Dark Red / Dark Green / Dark Blue |
| **Neon** | `#000000` | Hot Pink / Neon Green / Cyan |
| **Cyberpunk** | `#120d21` | Magenta / Electric Green / Cyan |

---

## 🖱️ Usage

| Action | How |
|---|---|
| **Move widget** | Click and drag |
| **Open menu** | Right-click |
| **Lock position** | Right-click → Lock Position |
| **Switch theme** | Right-click → Theme → select |
| **Switch interface** | Right-click → Network Interface → select |
| **Pause monitoring** | Right-click → Pause/Resume |
| **View data stats** | Right-click → Data Usage Stat |
| **Show/Hide** | Click the system tray icon |
| **Exit** | Right-click → Exit (or tray → Exit) |

---

## ⚙️ Configuration

The widget currently stores no persistent configuration. All settings (theme, position, selected interface) reset on restart.

---

## 🧪 Diagnostic Tool

Run `verify_logic.py` to test interface detection on your machine:

```bash
python verify_logic.py
```

This will list all network interfaces, identify Wi-Fi adapters, and verify that `psutil` can read I/O counters for them.

---

## 📝 Version History

| Version | Changes |
|---|---|
| **v0.2** | Bug fixes, security hardening, docstrings, thread safety, README |
| **v0.1** | Initial release with core monitoring features |

---

## 👤 Author

**Hishan Umayanga**

---

## 📄 License

This project is available for personal use. See the repository for license details.
