# ⚡ ARITERMINAL

A premium, high-performance terminal UI for Windows, built with Python and CustomTkinter. Ariterminal allows you to manage multiple terminal sessions in a single, beautiful interface with advanced log filtering, search, and session management.

## ✨ Features

- **🚀 Multi-Session Management**: Open and group multiple terminal instances (CMD, PowerShell, or Git Bash) in one window.
- **🔍 Advanced Search**: Instant, case-insensitive keyword search with match navigation.
- **🛡️ Admin Awareness**: Easily identify and launch administrator sessions with clear visual cues.
- **🎨 Premium UI**: Optimized dark theme with "Roboto Regular" typography and High-DPI awareness for crystal-clear text on any display.
- **📊 Log Filtering**: Interactive toggles to filter logs by level (INFO, WARN, ERROR, DEBUG, TRACE) in real-time.
- **💾 Session Safety**: Built-in confirmation dialogs to prevent accidental log deletion.
- **📂 Grouping & Organization**: Tag and group sessions to stay organized during complex workflows.

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- `customtkinter`
- `pillow`

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/ari-tive/ariterminal.git
   cd ariterminal
   ```
2. Install dependencies:
   ```bash
   pip install customtkinter pillow
   ```
3. Run the application:
   ```bash
   python terminal.py
   ```

## 🏗️ Building Executable
To build a standalone `.exe` for Windows:
```bash
pip install pyinstaller
pyinstaller --noconfirm terminal.spec
```
The executable will be generated in the `dist/` folder.

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
