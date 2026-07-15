"""PawPal+ core implementation.

Four classes:
  Task      - a single pet-care activity (description, time, frequency, status).
  Pet       - pet details plus its own list of tasks.
  Owner     - manages multiple pets and exposes all of their tasks.
  Scheduler - the "brain": retrieves, organizes, and schedules tasks across pets.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

# Priority label -> numeric weight. Higher = scheduled sooner.
PRIORITY_SCORES = {"high": 3, "medium": 2, "low": 1}


def _to_minutes(hhmm: str) -> int:
    """Convert a 'HH:MM' clock string to minutes-since-midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _safe_minutes(hhmm: str | None) -> int | None:
    """Parse 'HH:MM' to minutes-since-midnight, or None if missing/invalid."""
    if not hhmm:
        return None
    try:
        hours, minutes = hhmm.split(":")
        return int(hours) * 60 + int(minutes)
    except (ValueError, AttributeError):
        return None


def _to_hhmm(minutes: int) -> str:
    """Convert minutes-since-midnight back to a 'HH:MM' clock string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    name: str
    description: str
    duration: int                 # minutes
    frequency: str = "none"       # "none" | "daily" | "weekly"
    priority: str = "medium"      # "high" | "medium" | "low"
    preferred_time: str = ""      # "HH:MM", the task's desired time
    pet_name: str = ""            # stamped by Pet.add_task
    due_date: date | None = None  # calendar day the task is due
    is_completed: bool = False
    start_time: str | None = None  # assigned by the Scheduler

    def mark_completed(self) -> "Task | None":
        """Mark this task done; return its next occurrence if recurring.

        Returns None when the task was already completed, so processing the
        same completed task twice never creates duplicate follow-ups.
        """
        if self.is_completed:
            return None
        self.is_completed = True
        return self._next_occurrence()

    def _next_occurrence(self) -> "Task | None":
        """Build the next incomplete task for a daily/weekly recurrence."""
        if self.frequency not in ("daily", "weekly") or self.due_date is None:
            return None
        step = timedelta(days=1 if self.frequency == "daily" else 7)
        # replace() copies pet_name, title, duration, priority, time, frequency.
        return replace(
            self,
            is_completed=False,
            due_date=self.due_date + step,
            start_time=None,
        )

    def get_priority_score(self) -> int:
        """Numeric priority, defaulting to lowest for unknown labels."""
        return PRIORITY_SCORES.get(self.priority.lower(), 1)

    def fits_within_time(self, remaining_time: int) -> bool:
        """Return True if this task fits in the remaining minutes."""
        return self.duration <= remaining_time


@dataclass
class Pet:
    name: str
    animal_type: str
    breed: str = ""
    age: int = 0
    special_needs: list = field(default_factory=list)
    tasks: list = field(default_factory=list)

    def update_information(self, **fields) -> None:
        """Update any provided attributes, e.g. update_information(age=4)."""
        for key, value in fields.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_special_need(self, need: str) -> None:
        """Add a special need, ignoring duplicates."""
        if need not in self.special_needs:
            self.special_needs.append(need)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet, stamping it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self, include_completed: bool = True) -> list:
        """Return this pet's tasks, optionally excluding completed ones."""
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.is_completed]


@dataclass
class Owner:
    name: str
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self, include_completed: bool = True) -> list:
        """Flatten tasks across every pet, tagging each with its pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks(include_completed=include_completed))
        return all_tasks

    def get_pending_tasks(self) -> list:
        """Return every not-yet-completed task across all pets."""
        return self.get_all_tasks(include_completed=False)


class Scheduler:
    """Retrieves tasks from an Owner and builds a time-boxed daily plan."""

    def __init__(self, owner: Owner, available_time: int,
                 start_time: str = "08:00"):
        """Set up the scheduler for one owner's daily time budget."""
        self.owner = owner
        self.available_time = available_time   # minutes available today
        self.start_time = start_time           # "HH:MM"
        self._decisions: dict[str, str] = {}   # task name -> reason

    def collect_tasks(self) -> list:
        """Pull every pending task across all of the owner's pets."""
        return self.owner.get_pending_tasks()

    def sort_tasks(self, tasks: list) -> list:
        """Highest priority first; earlier preferred_time breaks ties."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.get_priority_score(),
                _to_minutes(t.preferred_time) if t.preferred_time else 24 * 60,
            ),
        )

    def filter_tasks(self, tasks: list) -> list:
        """Drop anything already completed or with no positive duration."""
        return [t for t in tasks if not t.is_completed and t.duration > 0]

    def sort_by_time(self) -> list:
        """Return a NEW list of all tasks sorted by preferred_time.

        Invalid or missing times sort to the end. The original task lists
        are not modified because sorted() builds a fresh list.
        """
        return sorted(
            self.owner.get_all_tasks(),
            key=lambda t: (
                _safe_minutes(t.preferred_time) is None,   # False(0) before True(1)
                _safe_minutes(t.preferred_time) or 0,      # then by clock time
            ),
        )

    def filter_by_pet(self, pet_name: str) -> list:
        """Return every task belonging to the named pet.

        Matching is case-insensitive, so "rex", "Rex", and "REX" all match a
        pet named "Rex". Returns a list of Task objects (empty if none match).
        """
        target = pet_name.lower()
        return [t for t in self.owner.get_all_tasks()
                if t.pet_name.lower() == target]

    def filter_by_status(self, is_completed: bool) -> list:
        """Return tasks matching the given completion status.

        Pass True for completed tasks or False for incomplete ones. Returns a
        list of Task objects (empty if none match).
        """
        return [t for t in self.owner.get_all_tasks()
                if t.is_completed == is_completed]

    def detect_conflicts(self) -> list:
        """Return (task_a, task_b) pairs that overlap in time.

        Only tasks on the same pet and same due_date are compared. Tasks that
        merely touch (one ends exactly when the next begins) do NOT conflict.
        Tasks with missing/invalid times are skipped rather than crashing.
        """
        conflicts = []
        tasks = self.owner.get_all_tasks()
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                if a.pet_name.lower() != b.pet_name.lower():
                    continue
                if a.due_date != b.due_date:
                    continue
                a_start = _safe_minutes(a.preferred_time)
                b_start = _safe_minutes(b.preferred_time)
                if a_start is None or b_start is None:
                    continue
                a_end, b_end = a_start + a.duration, b_start + b.duration
                # Overlap iff each starts before the other ends (strict).
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    def check_time_conflicts(self) -> list[str]:
        """Lightweight check for tasks sharing the exact same time slot.

        Compares every pair of incomplete tasks on the same due date, across
        all pets (same pet OR different pets), and returns a warning string
        for each pair that starts at the same preferred_time. Returns an empty
        list when there are no clashes. Never raises: tasks with missing or
        invalid times are skipped instead of crashing the program.
        """
        warnings: list[str] = []
        tasks = [t for t in self.owner.get_all_tasks() if not t.is_completed]
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                if a.due_date != b.due_date:
                    continue
                ta = _safe_minutes(a.preferred_time)
                tb = _safe_minutes(b.preferred_time)
                if ta is None or tb is None or ta != tb:
                    continue
                who = (a.pet_name if a.pet_name.lower() == b.pet_name.lower()
                       else f"{a.pet_name} and {b.pet_name}")
                warnings.append(
                    f"WARNING: '{a.name}' and '{b.name}' for {who} are both "
                    f"scheduled at {a.preferred_time}."
                )
        return warnings

    def assign_start_times(self, scheduled: list) -> None:
        """Lay scheduled tasks back-to-back starting at self.start_time."""
        cursor = _to_minutes(self.start_time)
        for task in scheduled:
            task.start_time = _to_hhmm(cursor)
            cursor += task.duration

    def generate_plan(self) -> dict:
        """Greedily fit the highest-priority tasks into the available time."""
        self._decisions.clear()
        candidates = self.sort_tasks(self.filter_tasks(self.collect_tasks()))

        scheduled, skipped = [], []
        remaining = self.available_time
        for task in candidates:
            if task.fits_within_time(remaining):
                scheduled.append(task)
                remaining -= task.duration
                self._decisions[task.name] = (
                    f"Scheduled: priority {task.priority} "
                    f"(score {task.get_priority_score()}), "
                    f"{task.duration} min fit within {remaining + task.duration} min left."
                )
            else:
                skipped.append(task)
                self._decisions[task.name] = (
                    f"Skipped: needs {task.duration} min but only "
                    f"{remaining} min remained."
                )

        self.assign_start_times(scheduled)
        return {
            "start_time": self.start_time,
            "total_available_time": self.available_time,
            "total_scheduled_time": self.available_time - remaining,
            "remaining_time": remaining,
            "scheduled_tasks": scheduled,
            "skipped_tasks": skipped,
        }

    def explain_decision(self, task: Task) -> str:
        """Return the recorded reason a task was scheduled or skipped."""
        return self._decisions.get(
            task.name, "No decision recorded; run generate_plan() first."
        )
