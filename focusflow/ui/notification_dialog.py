"""
Custom always-on-top task change notification dialog.
This dialog appears centered on screen when a task transition occurs.
It must be dismissed by clicking "Got it" — it will not close on its own.
"""

import tkinter as tk


# Colors matching the overlay theme
COLORS = {
    "work": "#3b82f6",
    "break": "#f59e0b",
    "lunch": "#f97316",
}
BG_COLOR = "#1a1a2e"
TEXT_COLOR = "#e8e8f0"


class NotificationDialog:
    """Shows a modal-like always-on-top notification for task transitions."""

    MAX_DISPLAY_CHARS = 35

    def __init__(self, parent: tk.Tk):
        self._parent = parent
        self._dialog: tk.Toplevel | None = None
        self._tooltip: tk.Toplevel | None = None

    def show(self, task_name: str, time_range: str, task_type: str) -> None:
        """Display the notification dialog. Closes any existing one first."""
        self.dismiss()

        self._dialog = tk.Toplevel(self._parent)
        dlg = self._dialog
        dlg.title("FocusFlow")
        dlg.configure(bg=BG_COLOR)
        dlg.overrideredirect(True)
        dlg.attributes("-topmost", True)

        width, height = 360, 180
        screen_w = dlg.winfo_screenwidth()
        screen_h = dlg.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        dlg.geometry(f"{width}x{height}+{x}+{y}")

        # Prevent closing via Alt+F4 without button
        dlg.protocol("WM_DELETE_WINDOW", self.dismiss)

        accent = COLORS.get(task_type, COLORS["work"])

        # Top accent bar
        bar = tk.Frame(dlg, bg=accent, height=4)
        bar.pack(fill="x")

        # Header
        header = tk.Label(
            dlg,
            text="Next Task",
            font=("Segoe UI", 11),
            fg="#888899",
            bg=BG_COLOR,
        )
        header.pack(pady=(16, 4))

        # Task name — truncate if too long, show full name on hover
        if len(task_name) > self.MAX_DISPLAY_CHARS:
            display_name = task_name[: self.MAX_DISPLAY_CHARS] + "…"
        else:
            display_name = task_name

        name_label = tk.Label(
            dlg,
            text=display_name,
            font=("Segoe UI Semibold", 16),
            fg=accent,
            bg=BG_COLOR,
        )
        name_label.pack(pady=(0, 4))

        if len(task_name) > self.MAX_DISPLAY_CHARS:
            name_label.bind(
                "<Enter>",
                lambda e: self._show_tooltip(e, task_name, accent),
            )
            name_label.bind("<Leave>", lambda e: self._hide_tooltip())

        # Time range
        time_label = tk.Label(
            dlg,
            text=time_range,
            font=("Segoe UI", 10),
            fg="#666677",
            bg=BG_COLOR,
        )
        time_label.pack()

        # Dismiss button
        btn = tk.Button(
            dlg,
            text="Got it",
            font=("Segoe UI", 11),
            fg=BG_COLOR,
            bg=accent,
            activebackground=accent,
            activeforeground=BG_COLOR,
            relief="flat",
            cursor="hand2",
            padx=24,
            pady=4,
            command=self.dismiss,
        )
        btn.pack(pady=(12, 0))

        # Keep focus — but do NOT grab_set() as that can interfere with
        # the root window and cause the app to close when the dialog is dismissed.
        dlg.focus_force()

        # Re-raise periodically in case something covers it
        self._keep_on_top()

    def dismiss(self) -> None:
        """Close the notification dialog."""
        self._hide_tooltip()
        if self._dialog is not None:
            try:
                self._dialog.destroy()
            except tk.TclError:
                pass
            self._dialog = None

    def _show_tooltip(self, event: tk.Event, full_text: str, accent: str) -> None:
        """Show full task name in a tooltip below the label."""
        self._hide_tooltip()
        if self._dialog is None:
            return
        x = self._dialog.winfo_x() + 20
        y = self._dialog.winfo_y() + self._dialog.winfo_height() + 4
        self._tooltip = tk.Toplevel(self._dialog)
        self._tooltip.overrideredirect(True)
        self._tooltip.attributes("-topmost", True)
        self._tooltip.configure(bg=accent)
        label = tk.Label(
            self._tooltip,
            text=full_text,
            font=("Segoe UI", 10),
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            padx=8,
            pady=4,
            wraplength=320,
        )
        label.pack(padx=1, pady=1)
        self._tooltip.geometry(f"+{x}+{y}")

    def _hide_tooltip(self) -> None:
        """Destroy the tooltip if it exists."""
        if self._tooltip is not None:
            try:
                self._tooltip.destroy()
            except tk.TclError:
                pass
            self._tooltip = None

    def _keep_on_top(self) -> None:
        """Periodically re-assert topmost status while dialog is open."""
        if self._dialog is not None:
            try:
                self._dialog.attributes("-topmost", True)
                self._dialog.lift()
                self._dialog.after(500, self._keep_on_top)
            except tk.TclError:
                pass
