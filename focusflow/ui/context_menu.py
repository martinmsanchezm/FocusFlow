"""
Right-click context menu for the FocusFlow overlay.
Provides access to Import, Export, transparency, and other settings.
"""

import tkinter as tk


class ContextMenu:
    """Builds and shows the right-click context menu."""

    def __init__(self, parent: tk.Tk, callbacks: dict):
        """
        callbacks should be a dict with keys:
          import_schedule, export_schedule, export_template,
          toggle_transparency, toggle_topmost, show_about, exit_app
        """
        self._parent = parent
        self._callbacks = callbacks
        self._menu = tk.Menu(
            parent,
            tearoff=0,
            bg="#1e1e2e",
            fg="#ccccdd",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
        )
        self._build()

    def _build(self) -> None:
        m = self._menu
        m.add_command(label="\U0001f4c5 Ver Agenda Semanal", command=self._callbacks["show_agenda"])
        m.add_separator()
        m.add_command(label="Import Schedule", command=self._callbacks["import_schedule"])
        m.add_command(label="Export Current Schedule", command=self._callbacks["export_schedule"])
        m.add_command(label="Export Blank Template", command=self._callbacks["export_template"])
        m.add_separator()
        m.add_command(label="Toggle Transparency", command=self._callbacks["toggle_transparency"])
        m.add_command(label="Always on Top: On/Off", command=self._callbacks["toggle_topmost"])
        m.add_separator()
        m.add_command(label="About", command=self._callbacks["show_about"])
        m.add_command(label="Exit", command=self._callbacks["exit_app"])

    def show(self, event: tk.Event) -> None:
        """Display the context menu at the cursor position."""
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass
