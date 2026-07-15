"""Automated test suite for the PawPal+ core classes."""

import os
import sys
from datetime import date, timedelta

# Allow running from anywhere by putting the project root on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagrams.pawpal_system import Owner, Pet, Scheduler, Task


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def make_scheduler(pets):
    """Wrap the given pets in an Owner + Scheduler for convenience."""
    owner = Owner("Tester", pets=list(pets))
    return Scheduler(owner, available_time=120, start_time="07:00")


# --------------------------------------------------------------------------
# Original smoke tests
# --------------------------------------------------------------------------
def test_task_completion():
    """Calling mark_completed() flips the task's status to done."""
    task = Task("Walk", "Evening walk", 30)
    assert task.is_completed is False

    task.mark_completed()

    assert task.is_completed is True


def test_task_addition():
    """Adding a task to a Pet increases that pet's task count."""
    pet = Pet("Rex", "dog", "Labrador", age=3)
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Feed", "Morning kibble", 10))

    assert len(pet.get_tasks()) == 1


# --------------------------------------------------------------------------
# 1. Sorting correctness
# --------------------------------------------------------------------------
def test_sort_by_time_is_chronological():
    """sort_by_time() returns tasks ordered earliest -> latest."""
    pet = Pet("Rex", "dog")
    # Added out of order on purpose.
    pet.add_task(Task("C", "", 10, preferred_time="18:00"))
    pet.add_task(Task("A", "", 10, preferred_time="07:30"))
    pet.add_task(Task("B", "", 10, preferred_time="12:00"))
    scheduler = make_scheduler([pet])

    ordered = scheduler.sort_by_time()
    times = [t.preferred_time for t in ordered]

    assert times == ["07:30", "12:00", "18:00"]


def test_sort_by_time_puts_invalid_times_last():
    """Tasks with missing/invalid times sort to the end, not first."""
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Bad", "", 10, preferred_time=""))       # missing
    pet.add_task(Task("Good", "", 10, preferred_time="09:00"))  # valid
    scheduler = make_scheduler([pet])

    ordered = scheduler.sort_by_time()

    assert ordered[0].name == "Good"
    assert ordered[-1].name == "Bad"


def test_sort_by_time_does_not_mutate_original():
    """sorted() builds a new list, so the pet's own list is untouched."""
    pet = Pet("Rex", "dog")
    pet.add_task(Task("late", "", 10, preferred_time="18:00"))
    pet.add_task(Task("early", "", 10, preferred_time="06:00"))
    scheduler = make_scheduler([pet])

    scheduler.sort_by_time()  # discard result; we only care about side effects

    # Original order on the pet is still the insertion order.
    assert [t.name for t in pet.get_tasks()] == ["late", "early"]


# --------------------------------------------------------------------------
# 2. Recurrence logic
# --------------------------------------------------------------------------
def test_daily_task_creates_next_day():
    """Completing a daily task returns a fresh task due one day later."""
    today = date(2026, 7, 15)
    task = Task("Meds", "", 5, frequency="daily",
                preferred_time="08:00", due_date=today)

    next_task = task.mark_completed()

    assert task.is_completed is True          # original marked done
    assert next_task is not None              # a follow-up was created
    assert next_task.is_completed is False    # the new one is not done
    assert next_task.due_date == today + timedelta(days=1)
    # Original fields are preserved on the new task.
    assert next_task.name == "Meds"
    assert next_task.preferred_time == "08:00"
    assert next_task.frequency == "daily"


def test_weekly_task_creates_task_seven_days_later():
    """Completing a weekly task advances the due date by 7 days."""
    today = date(2026, 7, 15)
    task = Task("Vet", "", 60, frequency="weekly", due_date=today)

    next_task = task.mark_completed()

    assert next_task.due_date == today + timedelta(days=7)


def test_completing_twice_does_not_duplicate():
    """A second mark_completed() returns None (no duplicate follow-up)."""
    task = Task("Meds", "", 5, frequency="daily", due_date=date(2026, 7, 15))

    first = task.mark_completed()
    second = task.mark_completed()

    assert first is not None
    assert second is None


def test_non_recurring_task_spawns_nothing():
    """A frequency='none' task completes without creating a follow-up."""
    task = Task("One-off", "", 10, frequency="none", due_date=date(2026, 7, 15))

    assert task.mark_completed() is None


# --------------------------------------------------------------------------
# 3. Conflict detection
# --------------------------------------------------------------------------
def test_check_time_conflicts_flags_duplicate_times():
    """Two tasks at the exact same time produce a warning."""
    today = date(2026, 7, 15)
    rex = Pet("Rex", "dog")
    rex.add_task(Task("Walk", "", 30, preferred_time="08:00", due_date=today))
    mia = Pet("Mia", "cat")
    mia.add_task(Task("Feed", "", 10, preferred_time="08:00", due_date=today))
    scheduler = make_scheduler([rex, mia])

    warnings = scheduler.check_time_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_finds_overlap():
    """Overlapping ranges for the same pet are returned as a pair."""
    today = date(2026, 7, 15)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Feed", "", 30, preferred_time="07:00", due_date=today))
    pet.add_task(Task("Brush", "", 20, preferred_time="07:15", due_date=today))
    scheduler = make_scheduler([pet])

    conflicts = scheduler.detect_conflicts()

    assert len(conflicts) == 1


def test_touching_endpoints_do_not_conflict():
    """One task ending exactly when the next starts is NOT a conflict."""
    today = date(2026, 7, 15)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("A", "", 30, preferred_time="07:00", due_date=today))  # ends 07:30
    pet.add_task(Task("B", "", 30, preferred_time="07:30", due_date=today))  # starts 07:30
    scheduler = make_scheduler([pet])

    assert scheduler.detect_conflicts() == []


# --------------------------------------------------------------------------
# Edge cases
# --------------------------------------------------------------------------
def test_empty_pet_returns_empty_results():
    """A pet with no tasks never crashes the sorter or conflict checks."""
    scheduler = make_scheduler([Pet("Empty", "fish")])

    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []
    assert scheduler.check_time_conflicts() == []


def test_filter_by_pet_is_case_insensitive():
    """filter_by_pet matches regardless of letter case."""
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Walk", "", 30, preferred_time="08:00"))
    scheduler = make_scheduler([pet])

    assert len(scheduler.filter_by_pet("rex")) == 1
    assert len(scheduler.filter_by_pet("REX")) == 1
    assert len(scheduler.filter_by_pet("Mia")) == 0


def test_filter_by_status_splits_done_and_pending():
    """filter_by_status(True/False) returns the right subset."""
    pet = Pet("Rex", "dog")
    done = Task("Done", "", 10)
    done.mark_completed()
    pet.add_task(done)
    pet.add_task(Task("Pending", "", 10))
    scheduler = make_scheduler([pet])

    assert [t.name for t in scheduler.filter_by_status(True)] == ["Done"]
    assert [t.name for t in scheduler.filter_by_status(False)] == ["Pending"]


if __name__ == "__main__":
    # Run every test function in this module when invoked directly.
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok - {name}")
    print("All tests passed.")
