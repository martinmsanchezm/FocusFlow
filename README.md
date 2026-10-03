# FocusFlow

**A Pomodoro-style schedule tracker that runs as a compact always-on-top overlay on Windows. It reads a weekly JSON schedule and shows only the task that is active right now, synced to your system clock.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-informational)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![PyInstaller](https://img.shields.io/badge/Build-PyInstaller-blue)

---

## Overview

FocusFlow is a small desktop widget that keeps your current time block on screen: for example a work session, a break or lunch. It has no countdown timers or task lists. You define your week once in a JSON file, and the widget does three things:

- checks the clock every 10 seconds
- shows the block that matches the current day and time
- pops up a notification when the next block starts

## Features

- **Always-on-top** floating widget: 280×65 px, frameless, draggable and hidden from the taskbar and Alt-Tab. It uses Win32 extended window styles, so it stays on top.
- **Current task only**: no timers, no clutter. Long task names are cut short with an ellipsis, and the full name shows on hover.
- **Color-coded** by task type (see the table below).
- **Task transition alerts**: a centered, always-on-top dialog appears when a new task starts and stays until you click **Got it**.
- **Weekly agenda viewer**: a scrollable window with all 7 days. Today is highlighted and the active task is marked.
- **Right-click menu**: import/export, transparency, always-on-top toggle.
- **Remembers** the last schedule, window position and settings between sessions.
- **Adjustable transparency** (100% / 85% / 70%).
- **Per-monitor DPI awareness** on Windows for sharp text.

### Task types

| Type | Color |
|---|---|
| `work` | Blue |
| `break` | Amber |
| `lunch` | Orange |
| `study` | Purple |
| `free` | Green |
| `personal` | Pink |

Any other type string is accepted and shown in gray. When no block is active, the widget shows **Free time**. On a day with an empty list, it shows **Day off**.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python (3.10+ syntax, e.g. `str \| None`) |
| UI | Tkinter (bundled with Python on Windows) |
| Windows integration | `ctypes` + Win32 API (`SetWindowPos`, `SetLayeredWindowAttributes`, DPI awareness) |
| Packaging | PyInstaller 6.11.1 |

## Project Structure

```text
FocusFlow/
├── LICENSE                      # MIT
├── .gitignore
└── focusflow/
    ├── main.py                  # Entry point (works from source and from the PyInstaller bundle)
    ├── app.py                   # FocusFlowApp: wires UI, scheduler, notifier and config; 10 s polling
    ├── scheduler.py             # Schedule/TaskBlock, JSON validation, current-task lookup
    ├── notifier.py              # TransitionDetector: detects when the active task changes
    ├── config.py                # Persists settings to %APPDATA%/FocusFlow/config.json
    ├── schedule_template.json   # Example full-week schedule
    ├── focusflow.spec           # PyInstaller build spec (windowed, single .exe)
    ├── requirements.txt
    └── ui/
        ├── overlay.py           # Main floating widget
        ├── context_menu.py      # Right-click menu
        ├── notification_dialog.py
        └── agenda_window.py     # Weekly agenda viewer
```

## Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/nensanc/FocusFlow.git
cd FocusFlow/focusflow
pip install -r requirements.txt
```

> `tkinter` comes bundled with Python on Windows. You don't need any extra UI libraries. `requirements.txt` only contains PyInstaller, for building the `.exe`.

### 2. Run in development mode

```bash
cd focusflow
python main.py
```

### 3. Build the .exe

```bash
cd focusflow
pyinstaller focusflow.spec
```

The executable will be at `focusflow/dist/FocusFlow.exe`.

## First Launch

1. Run `FocusFlow.exe` (or `python main.py`).
2. Right-click the widget → **Import Schedule** → select your `.json` file. You can start from `focusflow/schedule_template.json`.
3. The widget shows your current task and floats on top of all windows.

## Editing Your Schedule

1. Right-click → **Export Blank Template** to get a starting JSON file.
2. Edit the file in any text editor and fill in each day's time blocks.
3. Right-click → **Import Schedule** → load the edited file.

### JSON format

```json
{
  "schedule": {
    "monday": [
      { "start": "08:00", "end": "10:00", "task": "Deep Work", "type": "work" },
      { "start": "10:00", "end": "10:15", "task": "Break", "type": "break" },
      { "start": "12:00", "end": "13:00", "task": "Lunch", "type": "lunch" }
    ],
    "tuesday": [],
    "...": []
  }
}
```

Validation rules applied on import:

- All seven days (`monday` … `sunday`) must be present. An empty array means a day off.
- Each block needs `start`, `end`, `task` and `type`.
- Times use 24-hour `HH:MM` format. A block is active from `start` (inclusive) to `end` (exclusive).

## Right-click Menu

| Option | Description |
|---|---|
| 📅 Ver Agenda Semanal | Open the weekly agenda viewer |
| Import Schedule | Load a JSON schedule file |
| Export Current Schedule | Save the current schedule to a file |
| Export Blank Template | Save a starter template |
| Toggle Transparency | Cycle: 100% → 85% → 70% |
| Always on Top: On/Off | Toggle topmost behavior |
| About | App info |
| Exit | Close the app |

## Config

Settings are saved to `%APPDATA%/FocusFlow/config.json` automatically (`~/.config/FocusFlow/config.json` on other platforms):

- Last loaded schedule path (auto-loaded on startup)
- Window position
- Opacity level
- Always-on-top state

## Notes and Limitations

- The app is designed for **Windows**. On other platforms it falls back to plain Tkinter `-topmost` / `-alpha` behavior.
- Blocks can't cross midnight, because each block is compared within a single day.
- The agenda window and its menu entry are in Spanish. The rest of the UI is in English.
- The notification dialog has its own colors only for `work`, `break` and `lunch`. Other types use the `work` color there.

## Author

**Martin Sanchez** ([@nensanc](https://github.com/nensanc))

## License

This project is licensed under the [MIT License](LICENSE).
