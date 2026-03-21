"""
Main overlay window for FocusFlow.
A compact, draggable, always-on-top widget that displays the current active task.
Uses Win32 API (SetWindowPos + extended styles) for persistent topmost on Windows.
"""

import sys
import tkinter as tk
from typing import Optional
from scheduler import TaskBlock


# Color scheme
BG_COLOR = "#111118"
BORDER_COLOR = "#2a2a3a"
TEXT_COLOR = "#e8e8f0"
TIME_COLOR = "#E0E0E0"
TASK_COLORS = {
    "work": "#3b82f6",
    "break": "#f59e0b",
    "lunch": "#f97316",
}
FREE_COLOR = "#6b7280"
DAY_OFF_COLOR = "#a78bfa"

# Win32 constants
_GWL_EXSTYLE = -20
_WS_EX_TOPMOST = 0x00000008
_WS_EX_TOOLWINDOW = 0x00000080
_WS_EX_LAYERED = 0x00080000
_HWND_TOPMOST = -1
_HWND_NOTOPMOST = -2
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_NOACTIVATE = 0x0010
_SWP_FLAGS = _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE
_LWA_ALPHA = 0x00000002


class OverlayWindow:
    """The main floating widget showing the current task."""

    def __init__(self, root: tk.Tk, config: dict):
        self._root = root
        self._config = config
        self._is_windows = sys.platform == "win32"
        self._hwnd = None

        # Configure the main window
        root.title("FocusFlow")
        root.overrideredirect(True)  # Frameless
        root.configure(bg=BG_COLOR)
        self._topmost = config.get("always_on_top", True)
        root.attributes("-topmost", self._topmost)

        # Position from saved config
        x = config.get("window_x", 100)
        y = config.get("window_y", 50)
        root.geometry(f"280x65+{x}+{y}")

        # Opacity setting
        self._opacity = config.get("opacity", 1.0)

        # Outer frame with subtle border effect
        self._outer = tk.Frame(root, bg=BORDER_COLOR, padx=1, pady=1)
        self._outer.pack(fill="both", expand=True)

        # Inner frame — tight padding to eliminate dead space
        self._inner = tk.Frame(self._outer, bg=BG_COLOR, padx=10, pady=4)
        self._inner.pack(fill="both", expand=True)

        # Accent bar at the top (thin colored line)
        self._accent_bar = tk.Frame(self._inner, bg=FREE_COLOR, height=3)
        self._accent_bar.pack(fill="x", pady=(0, 4))

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

        # Time range label — high contrast, solid color
        self._time_label = tk.Label(
            self._inner,
            text="",
            font=("Segoe UI", 10),
            fg=TIME_COLOR,
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

        # Bind FocusOut to re-assert topmost immediately when losing focus
        root.bind("<FocusOut>", lambda e: self._apply_win32_topmost())

        # After the window is rendered, apply Win32 styles and start the loop
        root.after(200, self._init_win32)

    # --- Task display ---

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
        self._topmost = on
        self._root.attributes("-topmost", on)
        if self._is_windows and self._hwnd:
            if on:
                self._apply_win32_topmost()
            else:
                self._remove_win32_topmost()

    def set_opacity(self, alpha: float) -> None:
        self._opacity = alpha
        if self._is_windows and self._hwnd:
            self._apply_win32_opacity()
        else:
            self._root.attributes("-alpha", alpha)

    def get_position(self) -> tuple[int, int]:
        """Return current window position."""
        return self._root.winfo_x(), self._root.winfo_y()

    def bind_right_click(self, callback) -> None:
        """Bind right-click to all overlay widgets."""
        for widget in (self._root, self._outer, self._inner, self._task_label, self._time_label, self._accent_bar):
            widget.bind("<ButtonPress-3>", callback)

    # --- Win32 always-on-top enforcement ---

    def _init_win32(self) -> None:
        """
        After the window is visible, grab the real HWND and apply
        extended window styles + topmost + opacity via Win32 API.
        """
        if not self._is_windows:
            self._root.attributes("-alpha", self._opacity)
            self._start_topmost_loop()
            return

        try:
            import ctypes
            self._user32 = ctypes.windll.user32
            # Force a render so winfo_id returns the real handle
            self._root.update_idletasks()
            self._hwnd = self._user32.GetParent(self._root.winfo_id())

            # Set extended styles: TOPMOST + TOOLWINDOW (hide from taskbar/alt-tab) + LAYERED
            style = self._user32.GetWindowLongW(self._hwnd, _GWL_EXSTYLE)
            self._user32.SetWindowLongW(
                self._hwnd, _GWL_EXSTYLE,
                style | _WS_EX_TOPMOST | _WS_EX_TOOLWINDOW | _WS_EX_LAYERED,
            )

            # Apply topmost via SetWindowPos
            self._apply_win32_topmost()

            # Apply opacity via SetLayeredWindowAttributes (text stays solid)
            self._apply_win32_opacity()

        except (AttributeError, OSError):
            # Fallback to tkinter-only approach
            self._hwnd = None
            self._root.attributes("-alpha", self._opacity)

        self._start_topmost_loop()

    def _apply_win32_topmost(self) -> None:
        """Force HWND_TOPMOST via SetWindowPos."""
        if not self._is_windows or not self._hwnd or not self._topmost:
            return
        try:
            self._user32.SetWindowPos(
                self._hwnd, _HWND_TOPMOST, 0, 0, 0, 0, _SWP_FLAGS,
            )
        except (AttributeError, OSError):
            pass

    def _remove_win32_topmost(self) -> None:
        """Remove HWND_TOPMOST."""
        if not self._is_windows or not self._hwnd:
            return
        try:
            self._user32.SetWindowPos(
                self._hwnd, _HWND_NOTOPMOST, 0, 0, 0, 0, _SWP_FLAGS,
            )
        except (AttributeError, OSError):
            pass

    def _apply_win32_opacity(self) -> None:
        """
        Set window opacity via Win32 SetLayeredWindowAttributes.
        This makes the entire window semi-transparent as a composition layer,
        but text rendered on top stays at full contrast visually.
        """
        if not self._is_windows or not self._hwnd:
            return
        try:
            alpha_byte = max(0, min(255, int(255 * self._opacity)))
            self._user32.SetLayeredWindowAttributes(
                self._hwnd, 0, alpha_byte, _LWA_ALPHA,
            )
            # Disable tkinter's own alpha to avoid double-application
            self._root.attributes("-alpha", 1.0)
        except (AttributeError, OSError):
            # Fallback
            self._root.attributes("-alpha", self._opacity)

    def _start_topmost_loop(self) -> None:
        """Re-assert topmost every 1 second to survive focus changes."""
        if self._topmost:
            self._root.attributes("-topmost", True)
            self._root.lift()
            self._apply_win32_topmost()
        self._root.after(1000, self._start_topmost_loop)

    # --- Dragging ---

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x_root - self._root.winfo_x()
        self._drag_data["y"] = event.y_root - self._root.winfo_y()

    def _on_drag_move(self, event: tk.Event) -> None:
        new_x = event.x_root - self._drag_data["x"]
        new_y = event.y_root - self._drag_data["y"]
        self._root.geometry(f"+{new_x}+{new_y}")
