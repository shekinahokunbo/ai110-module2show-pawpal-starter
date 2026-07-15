# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
============================================
           TODAY'S SCHEDULE
============================================
Start: 07:00   Available: 60 min

Scheduled:
  07:00  Morning walk     (30 min, high)
  07:30  Give medication  (5 min, high)
  07:35  Feed             (10 min, medium)

Skipped:
  - Grooming         Skipped: needs 20 min but only 15 min remained.
  - Playtime         Skipped: needs 25 min but only 15 min remained.
--------------------------------------------
Time used: 45 / 60 min (15 min free)
============================================
```

## 🧪 Testing PawPal+

Run the automated suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite in [`tests/test_pawpal.py`](tests/test_pawpal.py) has 15 tests across
the core scheduling behaviors:

- **Sorting correctness** — tasks come back in chronological order, invalid or
  missing times sort to the end, and the original task list is not mutated.
- **Recurrence logic** — completing a daily task creates a new task due one day
  later (and a weekly task seven days later), fields are preserved, and
  completing the same task twice does **not** create duplicates.
- **Conflict detection** — exact same-time tasks raise a warning, overlapping
  time ranges are flagged, and tasks that merely touch (one ends as the next
  begins) are correctly **not** flagged.
- **Filtering** — by pet (case-insensitive) and by completion status.
- **Edge cases** — a pet with no tasks and empty owners never crash the sorter
  or the conflict checks.

### Sample test output

```
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/shekinahokunbo/ai110-module2show-pawpal-starter
plugins: anyio-4.14.0
collected 15 items

tests/test_pawpal.py ...............                                     [100%]

============================== 15 passed in 0.01s ==============================
```

### Confidence Level: ★★★★☆ (4/5)

All 15 tests pass and cover the happy paths plus the important edge cases
(empty pets, invalid times, touching endpoints, duplicate completion). Held
back from 5/5 because a few contracts are not yet locked down — e.g.
`filter_by_pet()` does not trim whitespace (`" Rex "` won't match), conflict
detection is not yet exercised across large task sets, and there are no tests
for the Streamlit `app.py` integration layer.

## 📐 Smarter Scheduling

All scheduling logic lives in the `Scheduler` class (plus recurrence on `Task`)
in [`diagrams/pawpal_system.py`](diagrams/pawpal_system.py).

| Feature | Method | Notes |
|---------|--------|-------|
| Sort by priority (plan builder) | `Scheduler.sort_tasks()` | Highest priority first; earlier `preferred_time` breaks ties. |
| Sort by time | `Scheduler.sort_by_time()` | Orders all tasks by `preferred_time`; invalid/missing times go last. |
| Filter by pet | `Scheduler.filter_by_pet(pet_name)` | Case-insensitive match on the task's `pet_name`. |
| Filter by completion status | `Scheduler.filter_by_status(is_completed)` | `True` = completed tasks, `False` = incomplete. |
| Overlap conflict detection | `Scheduler.detect_conflicts()` | Same pet + same due date, comparing time *ranges*. |
| Same-time conflict warnings | `Scheduler.check_time_conflicts()` | Any pet; exact same start time; returns warning strings. |
| Recurring tasks | `Task.mark_completed()` | Completing a daily/weekly task spawns its next occurrence. |
| Daily plan generation | `Scheduler.generate_plan()` | Greedily time-boxes tasks into the available minutes. |

### Sorting behavior

- **`Scheduler.sort_by_time()`** returns a **new** list of every task sorted by
  its `preferred_time` (`"HH:MM"`). It uses `sorted()` with a lambda key that is
  a tuple `(time_is_invalid, minutes)`, so tasks with missing or malformed times
  sink to the end instead of crashing. The original task lists are never mutated.
- **`Scheduler.sort_tasks()`** is the plan builder's internal sort: highest
  priority score first, with earlier `preferred_time` breaking ties.

### Filtering behavior

- **`Scheduler.filter_by_pet(pet_name)`** returns all tasks for a given pet.
  Matching is case-insensitive (`"rex"` matches `"Rex"`).
- **`Scheduler.filter_by_status(is_completed)`** returns completed tasks when
  passed `True` and incomplete tasks when passed `False`.

### Conflict detection logic

Two complementary checks:

- **`Scheduler.detect_conflicts()`** — the thorough check. It compares tasks on
  the **same pet and same due date** by their time *ranges* (start +
  `duration`). Two tasks conflict when each starts before the other ends;
  tasks that merely touch (one ends exactly when the next begins) do **not**
  conflict. Returns a list of `(task_a, task_b)` pairs.
- **`Scheduler.check_time_conflicts()`** — the lightweight check. It flags
  incomplete tasks on the same due date that share the **exact same**
  `preferred_time`, across **any pet** (same or different), and returns
  human-readable **warning strings** rather than raising. Both methods skip
  tasks with missing/invalid times instead of crashing.

### Recurring task logic

`Task` carries a `frequency` (`"none"`, `"daily"`, or `"weekly"`) and a
`due_date`. When **`Task.mark_completed()`** is called:

- It marks the task completed and, for a `"daily"` or `"weekly"` task, returns a
  new incomplete `Task` for the next occurrence (due date advanced by
  `timedelta(days=1)` or `timedelta(days=7)`), preserving the pet, title,
  duration, priority, time, and frequency via `dataclasses.replace()`.
- Completing an **already-completed** task returns `None`, so processing the
  same task twice never creates duplicate follow-ups.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->