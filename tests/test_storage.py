import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from todo.models import Task
from todo import storage


def make_task(**kwargs) -> Task:
    defaults = {"id": 1, "title": "Test task"}
    return Task(**{**defaults, **kwargs})


class TestTaskFromDict(unittest.TestCase):
    def test_required_fields(self):
        t = Task.from_dict({"id": 1, "title": "Buy milk"})
        self.assertEqual(t.id, 1)
        self.assertEqual(t.title, "Buy milk")

    def test_optional_defaults(self):
        t = Task.from_dict({"id": 1, "title": "Buy milk"})
        self.assertFalse(t.done)
        self.assertIsNotNone(t.created_at)

    def test_done_preserved(self):
        t = Task.from_dict({"id": 1, "title": "Buy milk", "done": True})
        self.assertTrue(t.done)

    def test_extra_keys_ignored(self):
        t = Task.from_dict({"id": 1, "title": "Buy milk", "priority": "high"})
        self.assertEqual(t.title, "Buy milk")

    def test_missing_id_raises(self):
        with self.assertRaises(KeyError):
            Task.from_dict({"title": "No ID"})

    def test_missing_title_raises(self):
        with self.assertRaises(KeyError):
            Task.from_dict({"id": 1})


class TestStorage(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._path = Path(self._tmp.name) / "tasks.json"
        self._patcher = patch.object(storage, "STORAGE_PATH", self._path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp.cleanup()

    def test_load_returns_empty_when_no_file(self):
        self.assertEqual(storage.load(), [])

    def test_save_creates_file(self):
        storage.save([make_task()])
        self.assertTrue(self._path.exists())

    def test_save_writes_valid_json(self):
        storage.save([make_task(id=1, title="Buy milk")])
        data = json.loads(self._path.read_text())
        self.assertEqual(data[0]["title"], "Buy milk")

    def test_round_trip(self):
        tasks = [make_task(id=1, title="A"), make_task(id=2, title="B", done=True)]
        storage.save(tasks)
        reloaded = storage.load()
        self.assertEqual(len(reloaded), 2)
        self.assertEqual(reloaded[0].title, "A")
        self.assertTrue(reloaded[1].done)

    def test_load_preserves_all_fields(self):
        original = make_task(id=3, title="Check fields", done=True)
        storage.save([original])
        reloaded = storage.load()[0]
        self.assertEqual(reloaded.id, original.id)
        self.assertEqual(reloaded.title, original.title)
        self.assertEqual(reloaded.done, original.done)
        self.assertEqual(reloaded.created_at, original.created_at)

    def test_save_empty_list(self):
        storage.save([])
        self.assertEqual(storage.load(), [])

    def test_load_corrupt_json_exits(self):
        self._path.write_text("not valid json")
        with self.assertRaises(SystemExit):
            storage.load()


if __name__ == "__main__":
    unittest.main()
