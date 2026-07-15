"""Simple tests for the PawPal+ core classes."""

import os
import sys

# Allow running from anywhere by putting the project root on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagrams.pawpal_system import Pet, Task


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


if __name__ == "__main__":
    test_task_completion()
    test_task_addition()
    print("All tests passed.")
