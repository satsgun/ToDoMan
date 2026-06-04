# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app
python3 main.py <command>
python3 -m todo <command>

# Run all tests
python3 -m unittest discover -s tests -v

# Run a single test file
python3 -m unittest tests.test_cli -v
python3 -m unittest tests.test_storage -v

# Run a single test case
python3 -m unittest tests.test_cli.TestCmdAdd.test_add_creates_task -v
```

No build or lint step — zero external dependencies, stdlib only.

## Architecture

The app is a pure-stdlib CLI todo manager. Data flows: `cli.py` parses arguments → calls command functions → delegates to `storage.py` → reads/writes `~/.todoman.json`.

- **`todo/models.py`** — `Task` dataclass (`id`, `title`, `done`, `priority`, `created_at`). `Task.from_dict()` is the only deserializer; optional fields default gracefully so old JSON without them still loads. Extra keys are silently ignored.
- **`todo/storage.py`** — `load()` / `save()` against `STORAGE_PATH = ~/.todoman.json`. Both call `sys.exit()` on IO/JSON errors rather than raising. Tests patch `storage.STORAGE_PATH` to a temp file to isolate disk state.
- **`todo/cli.py`** — `argparse`-based subcommands (`add`, `list`, `done`, `delete`). Each `cmd_*` function accepts `argparse.Namespace`. `build_parser()` wires subcommands; `main()` is the entry point.
- **`main.py`** — thin shim that calls `todo.cli.main()`.
- **`todo/__main__.py`** — enables `python3 -m todo`.

### ID assignment

New task IDs are `max(existing ids, default=0) + 1`. IDs are never reused by skipping gaps — after deleting task #3 from [1,3], the next ID is 2 (max of remaining is 1).

### Testing pattern

All test classes patch `storage.STORAGE_PATH` with a `tempfile.TemporaryDirectory` path in `setUp`/`tearDown`. CLI command functions are called directly with `argparse.Namespace(...)` — no subprocess or parser invocation needed. When constructing a Namespace for `cmd_add`, include all fields argparse would set (e.g. `priority="medium"`) or the call will raise `AttributeError`.
