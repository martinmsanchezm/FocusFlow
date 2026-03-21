"""
Schedule loading and current-task detection logic.
Reads a JSON schedule file, validates it, and determines which task
is active at any given moment based on the system clock.
"""

import json
from datetime import datetime
from typing import Optional

VALID_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
VALID_TYPES = ["work", "break", "lunch"]


class TaskBlock:
    """Represents a single time block in the schedule."""

    def __init__(self, start: str, end: str, task: str, task_type: str):
        self.start_str = start
        self.end_str = end
        self.task = task
        self.task_type = task_type
        # Parse "HH:MM" into hour and minute for fast comparison
        h, m = start.split(":")
        self.start_hour, self.start_min = int(h), int(m)
        h, m = end.split(":")
        self.end_hour, self.end_min = int(h), int(m)

    def is_active(self, hour: int, minute: int) -> bool:
        """Return True if the given time falls within [start, end)."""
        current = hour * 60 + minute
        start = self.start_hour * 60 + self.start_min
        end = self.end_hour * 60 + self.end_min
        return start <= current < end

    def __repr__(self) -> str:
        return f"TaskBlock({self.start_str}-{self.end_str}: {self.task})"


class Schedule:
    """Holds the weekly schedule and provides current-task queries."""

    def __init__(self):
        # day_name (lowercase) -> list of TaskBlock
        self.days: dict[str, list[TaskBlock]] = {day: [] for day in VALID_DAYS}
        self.source_path: str = ""

    def get_current_task(self, now: Optional[datetime] = None) -> Optional[TaskBlock]:
        """Return the TaskBlock active right now, or None."""
        if now is None:
            now = datetime.now()
        day_name = now.strftime("%A").lower()
        for block in self.days.get(day_name, []):
            if block.is_active(now.hour, now.minute):
                return block
        return None

    def is_day_off(self, now: Optional[datetime] = None) -> bool:
        """Return True if today's schedule is empty (day off)."""
        if now is None:
            now = datetime.now()
        day_name = now.strftime("%A").lower()
        return len(self.days.get(day_name, [])) == 0

    def get_stats(self) -> dict:
        """Return a summary of loaded schedule for confirmation messages."""
        days_with_tasks = sum(1 for blocks in self.days.values() if blocks)
        total_tasks = sum(len(blocks) for blocks in self.days.values())
        return {"days": days_with_tasks, "tasks": total_tasks}


def validate_schedule(data: dict) -> list[str]:
    """
    Validate the schedule JSON structure. Returns a list of error messages.
    Empty list means the schedule is valid.
    """
    errors = []
    if not isinstance(data, dict):
        return ["Root element must be a JSON object"]
    if "schedule" not in data:
        return ["Missing 'schedule' key at root level"]
    schedule = data["schedule"]
    if not isinstance(schedule, dict):
        return ["'schedule' must be a JSON object"]

    for day in VALID_DAYS:
        if day not in schedule:
            errors.append(f"Missing day: {day}")
            continue
        blocks = schedule[day]
        if not isinstance(blocks, list):
            errors.append(f"'{day}' must be an array")
            continue
        for i, block in enumerate(blocks):
            prefix = f"{day}[{i}]"
            if not isinstance(block, dict):
                errors.append(f"{prefix}: must be an object")
                continue
            for key in ("start", "end", "task", "type"):
                if key not in block:
                    errors.append(f"{prefix}: missing '{key}'")
            if "start" in block and "end" in block:
                try:
                    _parse_time(block["start"])
                    _parse_time(block["end"])
                except ValueError as e:
                    errors.append(f"{prefix}: {e}")
            if "type" in block and block["type"] not in VALID_TYPES:
                errors.append(f"{prefix}: unknown type '{block['type']}' (expected: {VALID_TYPES})")
    return errors


def load_schedule(filepath: str) -> tuple[Optional[Schedule], list[str]]:
    """
    Load and validate a schedule JSON file.
    Returns (Schedule, []) on success, or (None, [errors]) on failure.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None, [f"File not found: {filepath}"]
    except json.JSONDecodeError as e:
        return None, [f"Invalid JSON: {e}"]
    except OSError as e:
        return None, [f"Cannot read file: {e}"]

    errors = validate_schedule(data)
    if errors:
        return None, errors

    schedule = Schedule()
    schedule.source_path = filepath
    for day in VALID_DAYS:
        for block_data in data["schedule"].get(day, []):
            block = TaskBlock(
                start=block_data["start"],
                end=block_data["end"],
                task=block_data["task"],
                task_type=block_data["type"],
            )
            schedule.days[day].append(block)
    return schedule, []


def get_blank_template() -> dict:
    """Return a blank schedule template with example entries for weekdays."""
    return {
        "schedule": {
            "monday": [
                {"start": "09:00", "end": "09:30", "task": "Morning Review", "type": "work"},
                {"start": "09:30", "end": "12:00", "task": "Deep Work", "type": "work"},
                {"start": "12:00", "end": "13:00", "task": "Lunch", "type": "lunch"},
                {"start": "13:00", "end": "17:00", "task": "Afternoon Work", "type": "work"},
            ],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": [],
        }
    }


def schedule_to_dict(schedule: Schedule) -> dict:
    """Convert a Schedule object back to a JSON-serializable dict."""
    data = {"schedule": {}}
    for day in VALID_DAYS:
        data["schedule"][day] = [
            {
                "start": block.start_str,
                "end": block.end_str,
                "task": block.task,
                "type": block.task_type,
            }
            for block in schedule.days[day]
        ]
    return data


def _parse_time(time_str: str) -> tuple[int, int]:
    """Parse 'HH:MM' and return (hour, minute). Raises ValueError on bad format."""
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: '{time_str}' (expected HH:MM)")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Time out of range: '{time_str}'")
    return h, m
