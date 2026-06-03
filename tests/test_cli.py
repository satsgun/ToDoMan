import argparse
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import patch

from todo import storage
from todo.cli import cmd_add


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
