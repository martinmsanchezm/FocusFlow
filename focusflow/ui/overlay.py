"""
Main overlay window for FocusFlow.
A compact, draggable, always-on-top widget that displays the current active task.
"""

import tkinter as tk
from typing import Optional
from scheduler import TaskBlock


# Color scheme
BG_COLOR = "#111118"
BORDER_COLOR = "#2a2a3a"
TEXT_COLOR = "#e8e8f0"
SUBTEXT_COLOR = "#666677"
TASK_COLORS = {
    "work": "#3b82f6",
    "break": "#f59e0b",
    "lunch": "#f97316",
}
FREE_COLOR = "#6b7280"
DAY_OFF_COLOR = "#a78bfa"


class OverlayWindow:
    """The main floating widget showing the current task."""

    def __init__(self, root: tk.Tk, config: dict):
        self._root = root
        self._config = config

        # Configure the main window
        root.title("FocusFlow")
        root.overrideredirect(True)  # Frameless
        root.configure(bg=BG_COLOR)
        root.attributes("-topmost", config.get("always_on_top", True))
        root.attributes("-alpha", config.get("opacity", 1.0))

        # Position from saved config
        x = config.get("window_x", 100)
        y = config.get("window_y", 50)
        root.geometry(f"280x90+{x}+{y}")

        # Outer frame with subtle border effect
        self._outer = tk.Frame(root, bg=BORDER_COLOR, padx=1, pady=1)
        self._outer.pack(fill="both", expand=True)

        # Inner frame
        self._inner = tk.Frame(self._outer, bg=BG_COLOR, padx=12, pady=8)
        self._inner.pack(fill="both", expand=True)

        # Accent bar at the top (thin colored line)
        self._accent_bar = tk.Frame(self._inner, bg=FREE_COLOR, height=3)
        self._accent_bar.pack(fill="x", pady=(0, 6))

        # Task name label
        self._task_label = tk.Label(
            self._inner,
            text="Loading...",
            font=("Segoe UI Semibold", 13),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            anchor="w",
        )
        self._task_label.pack(fill="x")

        # Time range label
        self._time_label = tk.Label(
            self._inner,
            text="",
            font=("Segoe UI", 9),
            fg=SUBTEXT_COLOR,
            bg=BG_COLOR,
            anchor="w",
        )
        self._time_label.pack(fill="x")

        # Dragging state
        self._drag_data = {"x": 0, "y": 0}

        # Bind drag events to all widgets
        for widget in (root, self._outer, self._inner, self._task_label, self._time_label, self._accent_bar):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_move)

    def update_task(self, task: Optional[TaskBlock], is_day_off: bool) -> None:
        """Update the display with the current task or status."""
        if is_day_off:
            self._task_label.config(text="Day off  \U0001f389", fg=DAY_OFF_COLOR)
            self._time_label.config(text="No schedule today")
            self._accent_bar.config(bg=DAY_OFF_COLOR)
        elif task is None:
            self._task_label.config(text="Free time", fg=FREE_COLOR)
            self._time_label.config(text="No active task")
            self._accent_bar.config(bg=FREE_COLOR)
        else:
            color = TASK_COLORS.get(task.task_type, TASK_COLORS["work"])
            self._task_label.config(text=task.task, fg=color)
            self._time_label.config(text=f"{task.start_str} \u2013 {task.end_str}")
            self._accent_bar.config(bg=color)

    def set_topmost(self, on: bool) -> None:
        self._root.attributes("-topmost", on)

    def set_opacity(self, alpha: float) -> None:
        self._root.attributes("-alpha", alpha)

    def get_position(self) -> tuple[int, int]:
        """Return current window position."""
        return self._root.winfo_x(), self._root.winfo_y()

    def bind_right_click(self, callback) -> None:
        """Bind right-click to all overlay widgets."""
        for widget in (self._root, self._outer, self._inner, self._task_label, self._time_label, self._accent_bar):
            widget.bind("<ButtonPress-3>", callback)

    # --- Dragging ---

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x_root - self._root.winfo_x()
        self._drag_data["y"] = event.y_root - self._root.winfo_y()

    def _on_drag_move(self, event: tk.Event) -> None:
        new_x = event.x_root - self._drag_data["x"]
        new_y = event.y_root - self._drag_data["y"]
        self._root.geometry(f"+{new_x}+{new_y}")
