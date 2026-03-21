# FocusFlow

A Pomodoro-style schedule tracker that runs as a compact always-on-top overlay on Windows. It reads a JSON schedule and shows **only the current active task** synced to your system clock.

## Quick Start

### 1. Install dependencies

```bash
cd focusflow
pip install -r requirements.txt
```

> `tkinter` comes bundled with Python on Windows. No extra UI libraries needed.

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

1. Run `FocusFlow.exe` (or `python main.py`)
2. Right-click the widget → **Import Schedule** → select your `.json` file
3. The widget shows your current task and floats on top of all windows

## Editing Your Schedule

1. Right-click → **Export Blank Template** to get a starting JSON
2. Edit the file with any text editor — fill in each day's time blocks
3. Right-click → **Import Schedule** → load the edited file

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
    "..."
  }
}
```

Task types: `work`, `break`, `lunch`. Days with empty arrays show "Day off".

## Features

- **Always-on-top** floating widget (280x90px, frameless, draggable)
- **Current task only** — no timers, no clutter
- **Color-coded** by type (blue=work, amber=break, orange=lunch)
- **Task transition alerts** — modal notification when a new task starts
- **Right-click menu**: Import/Export, transparency toggle, always-on-top toggle
- **Remembers position** and settings between sessions
- **Adjustable transparency** (100% / 85% / 70%)

## Right-click Menu

| Option | Description |
|---|---|
| Import Schedule | Load a JSON schedule file |
| Export Current Schedule | Save current schedule to file |
| Export Blank Template | Save a starter template |
| Toggle Transparency | Cycle: 100% → 85% → 70% |
| Always on Top: On/Off | Toggle topmost behavior |
| About | App info |
| Exit | Close the app |

## Config

Settings are saved to `%APPDATA%/FocusFlow/config.json` automatically:
- Last loaded schedule path (auto-loaded on startup)
- Window position
- Opacity level
- Always-on-top state
