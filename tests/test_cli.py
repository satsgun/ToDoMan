import argparse
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import patch

from todo import storage
from todo.cli import cmd_add, cmd_delete, cmd_done, cmd_list
from todo.models import Task


class TestCmdAdd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _add(self, title: str):
        cmd_add(argparse.Namespace(title=title))

    def test_add_creates_task(self):
        self._add("Buy milk")
        tasks = storage.load()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Buy milk")

    def test_add_first_task_gets_id_one(self):
        self._add("First")
        self.assertEqual(storage.load()[0].id, 1)

    def test_add_increments_id(self):
        self._add("First")
        self._add("Second")
        ids = [t.id for t in storage.load()]
        self.assertEqual(ids, [1, 2])

    def test_add_done_defaults_false(self):
        self._add("New task")
        self.assertFalse(storage.load()[0].done)

    def test_add_persists_across_loads(self):
        self._add("Persisted")
        reloaded = storage.load()
        self.assertEqual(reloaded[0].title, "Persisted")

    def test_add_prints_confirmation(self):
        with unittest.mock.patch("builtins.print") as mock_print:
            self._add("Buy milk")
            mock_print.assert_called_once_with("Added task #1: Buy milk")


class TestCmdList(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _list(self):
        cmd_list(argparse.Namespace())

    def test_list_empty(self):
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            mock_print.assert_called_once_with(
                "No tasks yet. Use `todo add <title>` to create one."
            )

    def test_list_pending_task(self):
        storage.save([Task(id=1, title="Buy milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            mock_print.assert_called_once_with("[ ] #1  Buy milk")

    def test_list_done_task(self):
        storage.save([Task(id=1, title="Buy milk", done=True)])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            mock_print.assert_called_once_with("[x] #1  Buy milk")

    def test_list_multiple_tasks(self):
        storage.save([Task(id=1, title="A"), Task(id=2, title="B", done=True)])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            calls = [c.args[0] for c in mock_print.call_args_list]
            self.assertEqual(calls, ["[ ] #1  A", "[x] #2  B"])

    def test_list_preserves_order(self):
        storage.save([Task(id=2, title="Second"), Task(id=1, title="First")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            calls = [c.args[0] for c in mock_print.call_args_list]
            self.assertEqual(calls[0], "[ ] #2  Second")
            self.assertEqual(calls[1], "[ ] #1  First")


class TestCmdDone(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _done(self, task_id: int):
        cmd_done(argparse.Namespace(id=task_id))

    def test_marks_task_done(self):
        storage.save([Task(id=1, title="Buy milk")])
        self._done(1)
        self.assertTrue(storage.load()[0].done)

    def test_persists_done_flag(self):
        storage.save([Task(id=1, title="Buy milk")])
        self._done(1)
        self.assertTrue(storage.load()[0].done)

    def test_prints_confirmation(self):
        storage.save([Task(id=1, title="Buy milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._done(1)
            mock_print.assert_called_once_with("Marked task #1 as done.")

    def test_unknown_id_prints_error(self):
        storage.save([Task(id=1, title="Buy milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._done(99)
            mock_print.assert_called_once_with("Error: no task with ID 99.")

    def test_unknown_id_does_not_save(self):
        storage.save([Task(id=1, title="Buy milk")])
        self._done(99)
        self.assertFalse(storage.load()[0].done)

    def test_done_is_idempotent(self):
        storage.save([Task(id=1, title="Buy milk", done=True)])
        self._done(1)
        self.assertTrue(storage.load()[0].done)

    def test_only_target_task_is_marked(self):
        storage.save([Task(id=1, title="A"), Task(id=2, title="B")])
        self._done(1)
        tasks = storage.load()
        self.assertTrue(tasks[0].done)
        self.assertFalse(tasks[1].done)


class TestCmdDelete(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _delete(self, task_id: int):
        cmd_delete(argparse.Namespace(id=task_id))

    def test_delete_removes_task(self):
        storage.save([Task(id=1, title="Buy milk")])
        self._delete(1)
        self.assertEqual(storage.load(), [])

    def test_delete_prints_confirmation(self):
        storage.save([Task(id=1, title="Buy milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._delete(1)
            mock_print.assert_called_once_with("Deleted task #1.")

    def test_unknown_id_prints_error(self):
        storage.save([Task(id=1, title="Buy milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._delete(99)
            mock_print.assert_called_once_with("Error: no task with ID 99.")

    def test_unknown_id_does_not_modify_tasks(self):
        storage.save([Task(id=1, title="Buy milk")])
        self._delete(99)
        self.assertEqual(len(storage.load()), 1)

    def test_delete_only_removes_target(self):
        storage.save([Task(id=1, title="A"), Task(id=2, title="B")])
        self._delete(1)
        tasks = storage.load()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, 2)

    def test_add_after_delete_uses_max_existing_id(self):
        storage.save([Task(id=1, title="A"), Task(id=3, title="C")])
        self._delete(3)
        cmd_add(argparse.Namespace(title="D"))
        ids = [t.id for t in storage.load()]
        # max remaining id is 1, so next is 2 — no gap-skipping needed
        self.assertEqual(ids, [1, 2])
