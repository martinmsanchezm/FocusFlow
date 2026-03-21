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

    def __init__(self, parent: tk.Tk):
        self._parent = parent
        self._dialog: tk.Toplevel | None = None

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

        # Task name
        name_label = tk.Label(
            dlg,
            text=task_name,
            font=("Segoe UI Semibold", 16),
            fg=accent,
            bg=BG_COLOR,
            wraplength=320,
        )
        name_label.pack(pady=(0, 4))

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
        if self._dialog is not None:
            try:
                self._dialog.destroy()
            except tk.TclError:
                pass
            self._dialog = None

    def _keep_on_top(self) -> None:
        """Periodically re-assert topmost status while dialog is open."""
        if self._dialog is not None:
            try:
                self._dialog.attributes("-topmost", True)
                self._dialog.lift()
                self._dialog.after(500, self._keep_on_top)
            except tk.TclError:
                pass
