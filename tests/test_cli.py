import argparse
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import patch

from todo import storage
from todo.cli import build_parser, cmd_add, cmd_delete, cmd_done, cmd_list, positive_int, valid_date
from todo.models import Task


class TestPositiveInt(unittest.TestCase):
    def test_valid_positive(self):
        self.assertEqual(positive_int("1"), 1)
        self.assertEqual(positive_int("42"), 42)

    def test_zero_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("0")

    def test_negative_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("-5")

    def test_non_integer_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("abc")


class TestValidDate(unittest.TestCase):
    def test_valid_date_returned(self):
        self.assertEqual(valid_date("2026-06-10"), "2026-06-10")

    def test_wrong_format_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            valid_date("06/10/2026")

    def test_non_date_string_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            valid_date("tomorrow")

    def test_invalid_calendar_date_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            valid_date("2026-13-01")


class TestCmdAdd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _add(self, title: str, priority: str = "medium", due: str | None = None):
        cmd_add(argparse.Namespace(title=title, priority=priority, due=due))

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

    def test_add_blank_title_rejected(self):
        with self.assertRaises(SystemExit):
            self._add("")

    def test_add_whitespace_only_title_rejected(self):
        with self.assertRaises(SystemExit):
            self._add("   ")

    def test_add_strips_surrounding_whitespace(self):
        self._add("  Buy milk  ")
        self.assertEqual(storage.load()[0].title, "Buy milk")

    def test_add_default_priority_is_medium(self):
        self._add("Task")
        self.assertEqual(storage.load()[0].priority, "medium")

    def test_add_priority_high(self):
        self._add("Urgent", priority="high")
        self.assertEqual(storage.load()[0].priority, "high")

    def test_add_priority_low(self):
        self._add("Someday", priority="low")
        self.assertEqual(storage.load()[0].priority, "low")

    def test_add_invalid_priority_rejected(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["add", "Task", "--priority", "critical"])

    def test_add_due_date_stored(self):
        self._add("Buy milk", due="2099-12-31")
        self.assertEqual(storage.load()[0].due_date, "2099-12-31")

    def test_add_no_due_date_defaults_none(self):
        self._add("Buy milk")
        self.assertIsNone(storage.load()[0].due_date)

    def test_add_invalid_due_date_rejected(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["add", "Task", "--due", "06/10/2026"])


class TestCmdList(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _list(self, pending=False, search=None):
        cmd_list(argparse.Namespace(pending=pending, search=search))

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
            mock_print.assert_called_once_with("[ ] #1  Buy milk  [medium]")

    def test_list_done_task(self):
        storage.save([Task(id=1, title="Buy milk", done=True)])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            mock_print.assert_called_once_with("[x] #1  Buy milk  [medium]")

    def test_list_shows_priority(self):
        storage.save([Task(id=1, title="Urgent", priority="high")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            mock_print.assert_called_once_with("[ ] #1  Urgent  [high]")

    def test_list_sorted_by_priority(self):
        storage.save([
            Task(id=1, title="Low", priority="low"),
            Task(id=2, title="High", priority="high"),
            Task(id=3, title="Med", priority="medium"),
        ])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            calls = [c.args[0] for c in mock_print.call_args_list]
            self.assertEqual(calls[0], "[ ] #2  High  [high]")
            self.assertEqual(calls[1], "[ ] #3  Med  [medium]")
            self.assertEqual(calls[2], "[ ] #1  Low  [low]")

    def test_list_same_priority_preserves_insertion_order(self):
        storage.save([Task(id=2, title="Second"), Task(id=1, title="First")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            calls = [c.args[0] for c in mock_print.call_args_list]
            self.assertEqual(calls[0], "[ ] #2  Second  [medium]")
            self.assertEqual(calls[1], "[ ] #1  First  [medium]")

    def test_list_multiple_tasks(self):
        storage.save([Task(id=1, title="A"), Task(id=2, title="B", done=True)])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            calls = [c.args[0] for c in mock_print.call_args_list]
            self.assertEqual(calls, ["[ ] #1  A  [medium]", "[x] #2  B  [medium]"])

    def test_list_shows_due_date(self):
        storage.save([Task(id=1, title="Buy milk", due_date="2099-12-31")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            mock_print.assert_called_once_with("[ ] #1  Buy milk  [medium]  due:2099-12-31")

    def test_list_overdue_task_shown_in_red(self):
        storage.save([Task(id=1, title="Fix bug", due_date="2000-01-01")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            output = mock_print.call_args[0][0]
            self.assertTrue(output.startswith("\033[31m"))
            self.assertTrue(output.endswith("\033[0m"))
            self.assertIn("due:2000-01-01", output)

    def test_list_future_due_not_highlighted(self):
        storage.save([Task(id=1, title="Plan ahead", due_date="2099-12-31")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            self.assertNotIn("\033[31m", mock_print.call_args[0][0])

    def test_list_done_overdue_not_highlighted(self):
        storage.save([Task(id=1, title="Old task", done=True, due_date="2000-01-01")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            self.assertNotIn("\033[31m", mock_print.call_args[0][0])

    def test_list_no_due_date_not_highlighted(self):
        storage.save([Task(id=1, title="No due")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list()
            output = mock_print.call_args[0][0]
            self.assertNotIn("\033[31m", output)
            self.assertNotIn("due:", output)


class TestCmdListFilter(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def _list(self, pending=False, search=None):
        cmd_list(argparse.Namespace(pending=pending, search=search))

    def _printed_lines(self, mock_print):
        return [c.args[0] for c in mock_print.call_args_list]

    def test_pending_hides_done_tasks(self):
        storage.save([Task(id=1, title="Done", done=True), Task(id=2, title="Todo")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(pending=True)
            lines = self._printed_lines(mock_print)
            self.assertEqual(len(lines), 1)
            self.assertIn("#2", lines[0])

    def test_pending_with_all_done_prints_no_match(self):
        storage.save([Task(id=1, title="Done", done=True)])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(pending=True)
            mock_print.assert_called_once_with("No matching tasks.")

    def test_pending_with_no_tasks_prints_no_tasks(self):
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(pending=True)
            mock_print.assert_called_once_with(
                "No tasks yet. Use `todo add <title>` to create one."
            )

    def test_search_matches_keyword(self):
        storage.save([Task(id=1, title="Buy milk"), Task(id=2, title="Write tests")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(search="milk")
            lines = self._printed_lines(mock_print)
            self.assertEqual(len(lines), 1)
            self.assertIn("Buy milk", lines[0])

    def test_search_is_case_insensitive(self):
        storage.save([Task(id=1, title="Buy Milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(search="MILK")
            lines = self._printed_lines(mock_print)
            self.assertEqual(len(lines), 1)

    def test_search_no_match_prints_no_match(self):
        storage.save([Task(id=1, title="Buy milk")])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(search="groceries")
            mock_print.assert_called_once_with("No matching tasks.")

    def test_search_with_no_tasks_prints_no_tasks(self):
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(search="anything")
            mock_print.assert_called_once_with(
                "No tasks yet. Use `todo add <title>` to create one."
            )

    def test_pending_and_search_combined(self):
        storage.save([
            Task(id=1, title="Buy milk"),
            Task(id=2, title="Buy eggs", done=True),
            Task(id=3, title="Write tests"),
        ])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(pending=True, search="buy")
            lines = self._printed_lines(mock_print)
            self.assertEqual(len(lines), 1)
            self.assertIn("Buy milk", lines[0])

    def test_search_result_still_sorted_by_priority(self):
        storage.save([
            Task(id=1, title="Buy apples", priority="low"),
            Task(id=2, title="Buy oranges", priority="high"),
        ])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._list(search="buy")
            lines = self._printed_lines(mock_print)
            self.assertIn("Buy oranges", lines[0])
            self.assertIn("Buy apples", lines[1])


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

    def test_already_done_prints_notice(self):
        storage.save([Task(id=1, title="Buy milk", done=True)])
        with unittest.mock.patch("builtins.print") as mock_print:
            self._done(1)
            mock_print.assert_called_once_with("Task #1 is already done.")

    def test_already_done_does_not_save(self):
        storage.save([Task(id=1, title="Buy milk", done=True)])
        with patch.object(storage, "save") as mock_save:
            self._done(1)
            mock_save.assert_not_called()

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
        cmd_add(argparse.Namespace(title="D", priority="medium", due=None))
        ids = [t.id for t in storage.load()]
        # max remaining id is 1, so next is 2 — no gap-skipping needed
        self.assertEqual(ids, [1, 2])
