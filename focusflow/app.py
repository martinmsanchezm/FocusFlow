"""
Main application class for FocusFlow.
Wires together the overlay UI, scheduler, notifier, and config persistence.
Polls the system clock every 10 seconds to update the current task display.
"""

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from config import load_config, save_config
from scheduler import Schedule, load_schedule, schedule_to_dict, get_blank_template
from notifier import TransitionDetector
from ui.overlay import OverlayWindow
from ui.context_menu import ContextMenu
from ui.notification_dialog import NotificationDialog
from ui.agenda_window import AgendaWindow

POLL_INTERVAL_MS = 10_000  # 10 seconds


class FocusFlowApp:
    """Core application: ties together all components."""

    def __init__(self):
        self._config = load_config()
        self._schedule = Schedule()
        self._detector = TransitionDetector()

        # Create root window
        self._root = tk.Tk()

        # Enable DPI awareness on Windows
        self._set_dpi_awareness()

        # Build UI components
        self._overlay = OverlayWindow(self._root, self._config)
        self._notification = NotificationDialog(self._root)
        self._agenda = AgendaWindow(self._root)
        self._context_menu = ContextMenu(self._root, {
            "show_agenda": self._show_agenda,
            "import_schedule": self._import_schedule,
            "export_schedule": self._export_schedule,
            "export_template": self._export_template,
            "toggle_transparency": self._toggle_transparency,
            "toggle_topmost": self._toggle_topmost,
            "show_about": self._show_about,
            "exit_app": self._exit,
        })
        self._overlay.bind_right_click(self._context_menu.show)

        # Auto-load last used schedule
        last_path = self._config.get("last_schedule_path", "")
        if last_path and os.path.isfile(last_path):
            schedule, errors = load_schedule(last_path)
            if schedule and not errors:
                self._schedule = schedule

        # Save position on close
        self._root.protocol("WM_DELETE_WINDOW", self._exit)

        # Initial display update and start polling
        self._poll()

    def run(self) -> None:
        """Start the tkinter main loop."""
        self._root.mainloop()

    # --- Polling ---

    def _poll(self) -> None:
        """Check the current task and update the display. Runs every 10s."""
        current_task = self._schedule.get_current_task()
        is_day_off = self._schedule.is_day_off()

        self._overlay.update_task(current_task, is_day_off)

        # Detect task transitions and show notification
        if self._detector.check_transition(current_task) and current_task is not None:
            time_range = f"{current_task.start_str} \u2013 {current_task.end_str}"
            self._notification.show(current_task.task, time_range, current_task.task_type)

        self._root.after(POLL_INTERVAL_MS, self._poll)

    # --- Menu actions ---

    def _import_schedule(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Import Schedule",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filepath:
            return
        schedule, errors = load_schedule(filepath)
        if errors:
            messagebox.showerror("Import Error", "Invalid schedule file:\n\n" + "\n".join(errors[:10]))
            return
        self._schedule = schedule
        self._detector.reset()
        self._config["last_schedule_path"] = filepath
        self._save_state()
        stats = schedule.get_stats()
        messagebox.showinfo(
            "Schedule Loaded",
            f"Loaded {stats['tasks']} tasks across {stats['days']} days.",
        )
        # Refresh display immediately
        self._poll()

    def _export_schedule(self) -> None:
        filepath = filedialog.asksaveasfilename(
            title="Export Current Schedule",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not filepath:
            return
        data = schedule_to_dict(self._schedule)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Schedule saved to:\n{filepath}")
        except OSError as e:
            messagebox.showerror("Export Error", str(e))

    def _export_template(self) -> None:
        filepath = filedialog.asksaveasfilename(
            title="Export Blank Template",
            defaultextension=".json",
            initialfile="schedule_template.json",
            filetypes=[("JSON files", "*.json")],
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(get_blank_template(), f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Blank template saved to:\n{filepath}")
        except OSError as e:
            messagebox.showerror("Export Error", str(e))

    def _toggle_transparency(self) -> None:
        """Cycle opacity: 1.0 -> 0.85 -> 0.70 -> 1.0"""
        current = self._config.get("opacity", 1.0)
        if current >= 1.0:
            new_opacity = 0.85
        elif current >= 0.85:
            new_opacity = 0.70
        else:
            new_opacity = 1.0
        self._config["opacity"] = new_opacity
        self._overlay.set_opacity(new_opacity)
        self._save_state()

    def _toggle_topmost(self) -> None:
        current = self._config.get("always_on_top", True)
        new_state = not current
        self._config["always_on_top"] = new_state
        self._overlay.set_topmost(new_state)
        self._save_state()

    def _show_agenda(self) -> None:
        """Open the weekly agenda viewer."""
        self._agenda.show(self._schedule)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About FocusFlow",
            "FocusFlow v1.0\n\n"
            "A Pomodoro-style schedule tracker.\n"
            "Shows your current task based on\n"
            "the system clock and your schedule.\n\n"
            "Right-click to import/export schedules.",
        )

    def _exit(self) -> None:
        self._save_state()
        self._root.destroy()

    # --- Helpers ---

    def _save_state(self) -> None:
        """Persist current window position and settings."""
        x, y = self._overlay.get_position()
        self._config["window_x"] = x
        self._config["window_y"] = y
        save_config(self._config)

    @staticmethod
    def _set_dpi_awareness() -> None:
        """Enable per-monitor DPI awareness on Windows for crisp rendering."""
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (AttributeError, OSError):
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except (AttributeError, OSError):
                    pass
