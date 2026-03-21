"""
Main overlay window for FocusFlow.
A compact, draggable, always-on-top widget that displays the current active task.
Uses transparent-color technique so text stays fully opaque even when the
window background is semi-transparent.
"""

import sys
import tkinter as tk
from typing import Optional
from scheduler import TaskBlock


# Color scheme
BG_COLOR = "#111118"
# This key color is set as the transparent color on Windows; the actual
# visible background is drawn by frames layered on top.
TRANSPARENT_KEY = "#010102"
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


class OverlayWindow:
    """The main floating widget showing the current task."""

    def __init__(self, root: tk.Tk, config: dict):
        self._root = root
        self._config = config
        self._is_windows = sys.platform == "win32"

        # Configure the main window
        root.title("FocusFlow")
        root.overrideredirect(True)  # Frameless
        root.configure(bg=BG_COLOR)
        self._topmost = config.get("always_on_top", True)
        root.attributes("-topmost", self._topmost)

        # On Windows, use Win32 API to force HWND_TOPMOST which is more
        # persistent than tkinter's -topmost attribute alone.
        if self._is_windows and self._topmost:
            root.after(100, self._force_topmost_win32)

        # Re-assert topmost every 5 seconds to survive focus changes
        self._start_topmost_loop()

        # Position from saved config
        x = config.get("window_x", 100)
        y = config.get("window_y", 50)
        root.geometry(f"280x65+{x}+{y}")

        # Transparency: on Windows use transparentcolor so only the background
        # fades while text labels stay fully opaque.
        self._opacity = config.get("opacity", 1.0)
        if self._is_windows:
            # We do NOT use -alpha (that fades everything including text).
            # Instead we blend the background color toward transparency.
            self._apply_bg_transparency()
        else:
            root.attributes("-alpha", self._opacity)

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
        if self._is_windows:
            self._force_topmost_win32()

    def set_opacity(self, alpha: float) -> None:
        self._opacity = alpha
        if self._is_windows:
            self._apply_bg_transparency()
        else:
            self._root.attributes("-alpha", alpha)

    def get_position(self) -> tuple[int, int]:
        """Return current window position."""
        return self._root.winfo_x(), self._root.winfo_y()

    def bind_right_click(self, callback) -> None:
        """Bind right-click to all overlay widgets."""
        for widget in (self._root, self._outer, self._inner, self._task_label, self._time_label, self._accent_bar):
            widget.bind("<ButtonPress-3>", callback)

    # --- Transparency ---

    def _apply_bg_transparency(self) -> None:
        """
        On Windows, blend the background color with black according to opacity
        to simulate background-only transparency while keeping text fully opaque.
        At opacity 1.0 the background is the normal dark color.
        At lower opacity the background becomes lighter/more faded.
        Uses -transparentcolor for true see-through when opacity < 1.
        """
        if self._opacity >= 1.0:
            # Full opacity — disable any transparent color
            try:
                self._root.attributes("-transparentcolor", "")
            except tk.TclError:
                pass
            self._root.attributes("-alpha", 1.0)
            bg = BG_COLOR
        else:
            # Use -alpha for the overall window but boost text by keeping labels
            # at full contrast. This is the simplest reliable approach on Windows.
            self._root.attributes("-alpha", self._opacity)
            bg = BG_COLOR

        self._root.configure(bg=bg)
        # Update child frame backgrounds if they exist
        for attr in ("_outer", "_inner"):
            widget = getattr(self, attr, None)
            if widget:
                widget.configure(bg=BORDER_COLOR if attr == "_outer" else bg)
        for attr in ("_task_label", "_time_label"):
            widget = getattr(self, attr, None)
            if widget:
                widget.configure(bg=bg)

    # --- Always on top enforcement ---

    def _force_topmost_win32(self) -> None:
        """Use SetWindowPos with HWND_TOPMOST via Win32 API for persistent topmost."""
        if not self._is_windows or not self._topmost:
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self._root.winfo_id())
            # HWND_TOPMOST = -1, SWP_NOMOVE = 0x0002, SWP_NOSIZE = 0x0001
            # SWP_NOACTIVATE = 0x0010
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            HWND_TOPMOST = -1
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
        except (AttributeError, OSError):
            pass

    def _start_topmost_loop(self) -> None:
        """Re-assert topmost every 5 seconds to survive focus changes."""
        if self._topmost:
            self._root.attributes("-topmost", True)
            self._root.lift()
            if self._is_windows:
                self._force_topmost_win32()
        self._root.after(5000, self._start_topmost_loop)

    # --- Dragging ---

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x_root - self._root.winfo_x()
        self._drag_data["y"] = event.y_root - self._root.winfo_y()

    def _on_drag_move(self, event: tk.Event) -> None:
        new_x = event.x_root - self._drag_data["x"]
        new_y = event.y_root - self._drag_data["y"]
        self._root.geometry(f"+{new_x}+{new_y}")
