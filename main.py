"""PawPal+ terminal demo: sorting, filtering, recurrence, and conflicts."""

from datetime import date

from diagrams.pawpal_system import Owner, Pet, Scheduler, Task


def build_owner() -> Owner:
    """Create an owner with two pets and several deliberately unsorted tasks."""
    today = date.today()

    rex = Pet("Rex", "dog", "Labrador", age=3)
    # Added in the WRONG time order on purpose: 18:00, then 07:30, then 12:00.
    rex.add_task(Task("Evening walk", "", 30, priority="medium",
                      preferred_time="18:00", due_date=today))
    rex.add_task(Task("Morning meds", "", 5, frequency="daily",
                      priority="high", preferred_time="07:30", due_date=today))
    rex.add_task(Task("Lunch feed", "", 15, priority="medium",
                      preferred_time="12:00", due_date=today))

    mia = Pet("Mia", "cat", "Tabby", age=2)
    mia.add_task(Task("Vet visit", "", 60, frequency="weekly",
                      priority="high", preferred_time="09:00", due_date=today))
    # Two OVERLAPPING tasks for Mia: 07:00-07:30 and 07:15-07:35.
    mia.add_task(Task("Feed", "", 30, priority="medium",
                      preferred_time="07:00", due_date=today))
    mia.add_task(Task("Brush", "", 20, priority="low",
                      preferred_time="07:15", due_date=today))

    # Two tasks at the EXACT SAME time (08:00) on different pets -> clash.
    rex.add_task(Task("Breakfast", "", 10, priority="medium",
                      preferred_time="08:00", due_date=today))
    mia.add_task(Task("Breakfast", "", 10, priority="medium",
                      preferred_time="08:00", due_date=today))

    return Owner("Sam", pets=[rex, mia])


def section(title: str) -> None:
    """Print a labeled section header."""
    print("\n" + "=" * 54)
    print(title)
    print("=" * 54)


def show(tasks: list) -> None:
    """Print a list of tasks in a readable, aligned format."""
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        status = "done" if t.is_completed else "todo"
        print(f"  {t.preferred_time or '--:--'}  {t.name:<14} "
              f"{t.pet_name:<5} {t.duration:>3}m  {t.priority:<6} "
              f"[{status}] due {t.due_date}")


def main() -> None:
    owner = build_owner()
    scheduler = Scheduler(owner, available_time=120, start_time="07:00")

    # 1 + 2: two pets created above, tasks added in incorrect time order.
    section("1. All tasks sorted by time (added out of order)")
    show(scheduler.sort_by_time())

    section("2. Only Rex's tasks (case-insensitive: 'rex')")
    show(scheduler.filter_by_pet("rex"))

    section("3. Only incomplete tasks")
    show(scheduler.filter_by_status(False))

    section("4. Complete a DAILY task -> next day's task appears")
    rex = owner.get_pet("Rex")
    daily = next(t for t in rex.get_tasks() if t.name == "Morning meds")
    next_daily = daily.mark_completed()
    rex.add_task(next_daily)
    print(f"  Completed: {daily.name} (due {daily.due_date})")
    print(f"  Created:   {next_daily.name} (due {next_daily.due_date})")
    print(f"  Completing it again returns: {daily.mark_completed()}  (no duplicate)")

    section("5. Complete a WEEKLY task -> task 7 days later appears")
    mia = owner.get_pet("Mia")
    weekly = next(t for t in mia.get_tasks() if t.name == "Vet visit")
    next_weekly = weekly.mark_completed()
    mia.add_task(next_weekly)
    print(f"  Completed: {weekly.name} (due {weekly.due_date})")
    print(f"  Created:   {next_weekly.name} (due {next_weekly.due_date})")

    section("6. Conflict detection (overlapping times, same pet)")
    conflicts = scheduler.detect_conflicts()
    if not conflicts:
        print("  No conflicts found.")
    for a, b in conflicts:
        print(f"  CONFLICT for {a.pet_name}: "
              f"'{a.name}' ({a.preferred_time}, {a.duration}m) overlaps "
              f"'{b.name}' ({b.preferred_time}, {b.duration}m)")

    section("7. Same-time warnings (lightweight, any pet)")
    warnings = scheduler.check_time_conflicts()
    if not warnings:
        print("  No time conflicts.")
    for w in warnings:
        print(f"  {w}")


if __name__ == "__main__":
    main()
