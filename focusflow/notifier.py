"""
Task transition notification logic.
Detects when the active task changes and triggers an always-on-top
notification dialog that must be dismissed by the user.
"""

from scheduler import TaskBlock


class TransitionDetector:
    """
    Tracks the last known active task and detects transitions.
    A transition occurs when the current task differs from the previous one.
    """

    def __init__(self):
        self._last_task_key: str | None = None

    def check_transition(self, current_task: TaskBlock | None) -> bool:
        """
        Compare the current task to the last known task.
        Returns True if a transition just occurred.
        """
        current_key = self._make_key(current_task)
        if current_key != self._last_task_key:
            self._last_task_key = current_key
            return True
        return False

    def reset(self):
        """Reset the detector state (e.g., after importing a new schedule)."""
        self._last_task_key = None

    @staticmethod
    def _make_key(task: TaskBlock | None) -> str | None:
        """Create a unique key for a task block to compare identity."""
        if task is None:
            return None
        return f"{task.start_str}|{task.end_str}|{task.task}"
