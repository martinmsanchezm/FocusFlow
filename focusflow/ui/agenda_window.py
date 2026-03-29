"""
Weekly agenda viewer window for FocusFlow.
Shows all 7 days in a vertical scrollable list with color-coded task blocks.
The current day is highlighted and the active task is marked.
"""

import tkinter as tk
from datetime import datetime
from typing import Optional

from scheduler import Schedule, TaskBlock, VALID_DAYS

# Colors — same scheme as overlay
BG_COLOR = "#111118"
HEADER_BG = "#1a1a2e"
HEADER_FG = "#ccccdd"
TODAY_HEADER_BG = "#1e2a4a"
TODAY_HEADER_FG = "#3b82f6"
TEXT_COLOR = "#d0d0dd"
SUBTEXT_COLOR = "#888899"
ACTIVE_BG = "#1a2540"
FREE_DAY_COLOR = "#555566"
TASK_COLORS = {
    "work": "#3b82f6",
    "break": "#f59e0b",
    "lunch": "#f97316",
    "study": "#7B68EE",
    "free": "#5BAD6F",
    "personal": "#E0559A",
}

DAY_LABELS = {
    "monday": "Lunes",
    "tuesday": "Martes",
    "wednesday": "Miércoles",
    "thursday": "Jueves",
    "friday": "Viernes",
    "saturday": "Sábado",
    "sunday": "Domingo",
}


class AgendaWindow:
    """A Toplevel window that displays the full weekly schedule."""

    def __init__(self, parent: tk.Tk):
        self._parent = parent
        self._window: Optional[tk.Toplevel] = None

    def show(self, schedule: Schedule) -> None:
        """Open the agenda window, or bring it to front if already open."""
        if self._window is not None:
            try:
                self._window.lift()
                self._window.focus_force()
                return
            except tk.TclError:
                self._window = None

        now = datetime.now()
        today_name = now.strftime("%A").lower()

        self._window = tk.Toplevel(self._parent)
        win = self._window
        win.title("Agenda Semanal — FocusFlow")
        win.configure(bg=BG_COLOR)
        win.attributes("-topmost", True)
        win.geometry("520x600")
        win.minsize(400, 300)
        win.protocol("WM_DELETE_WINDOW", self._close)

        # Scrollable canvas setup
        container = tk.Frame(win, bg=BG_COLOR)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=BG_COLOR, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=BG_COLOR)

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Bind mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        win.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Detect current active task for highlighting
        current_task = schedule.get_current_task(now)

        # Build each day section
        for day in VALID_DAYS:
            is_today = day == today_name
            blocks = schedule.days.get(day, [])
            self._build_day_section(day, blocks, is_today, current_task, now)

        # Close button at bottom
        btn_frame = tk.Frame(win, bg=BG_COLOR, pady=8)
        btn_frame.pack(fill="x")
        close_btn = tk.Button(
            btn_frame,
            text="Cerrar",
            font=("Segoe UI", 10),
            fg=BG_COLOR,
            bg="#3b82f6",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=4,
            command=self._close,
        )
        close_btn.pack()

    def _build_day_section(
        self,
        day: str,
        blocks: list[TaskBlock],
        is_today: bool,
        current_task: Optional[TaskBlock],
        now: datetime,
    ) -> None:
        """Build one day's section in the scroll frame."""
        frame = self._scroll_frame

        # Day header
        header_bg = TODAY_HEADER_BG if is_today else HEADER_BG
        header_fg = TODAY_HEADER_FG if is_today else HEADER_FG
        header_font = ("Segoe UI Semibold", 12) if is_today else ("Segoe UI", 11)
        day_label = DAY_LABELS.get(day, day.capitalize())
        if is_today:
            day_label = f"\u25cf  {day_label}  —  Hoy"

        header = tk.Label(
            frame,
            text=day_label,
            font=header_font,
            fg=header_fg,
            bg=header_bg,
            anchor="w",
            padx=16,
            pady=6,
        )
        header.pack(fill="x", pady=(8, 0))

        if not blocks:
            empty = tk.Label(
                frame,
                text="\u2014 Día libre \u2014",
                font=("Segoe UI", 10),
                fg=FREE_DAY_COLOR,
                bg=BG_COLOR,
                anchor="w",
                padx=24,
                pady=4,
            )
            empty.pack(fill="x")
            return

        for block in blocks:
            # Determine if this block is the currently active task
            is_active = (
                is_today
                and current_task is not None
                and block.start_str == current_task.start_str
                and block.end_str == current_task.end_str
                and block.task == current_task.task
            )

            row_bg = ACTIVE_BG if is_active else BG_COLOR
            color = TASK_COLORS.get(block.task_type, "#888888")

            row = tk.Frame(frame, bg=row_bg)
            row.pack(fill="x")

            # Color indicator dot
            dot = tk.Label(
                row,
                text="\u25cf",
                font=("Segoe UI", 8),
                fg=color,
                bg=row_bg,
            )
            dot.pack(side="left", padx=(16, 4), pady=2)

            # Time range
            time_text = f"{block.start_str} \u2013 {block.end_str}"
            time_lbl = tk.Label(
                row,
                text=time_text,
                font=("Segoe UI", 9),
                fg=SUBTEXT_COLOR,
                bg=row_bg,
                width=13,
                anchor="w",
            )
            time_lbl.pack(side="left", pady=2)

            # Task name — bold if active
            task_font = ("Segoe UI Semibold", 10) if is_active else ("Segoe UI", 10)
            task_lbl = tk.Label(
                row,
                text=block.task,
                font=task_font,
                fg=color if is_active else TEXT_COLOR,
                bg=row_bg,
                anchor="w",
            )
            task_lbl.pack(side="left", fill="x", expand=True, pady=2)

    def _close(self) -> None:
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            self._window = None
