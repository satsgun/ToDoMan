# todoman

A minimal command-line to-do manager.

## Requirements

- Python 3.10+
- No external dependencies

## Installation

### As an installable package (recommended)

```bash
git clone <repo-url>
cd TodoMan_prj1
pip install -e .
```

After installation, run as:

```bash
todo <command>
```

Alternatively, use `pipx` for an isolated install:

```bash
pipx install .
```

### As a script (no install required)

```bash
git clone <repo-url>
cd TodoMan_prj1
python3 main.py <command>
# or
python3 -m todo <command>
```

## Usage

```
todo <command> [options]
```

### Commands

| Command | Description |
|---|---|
| `add <title>` | Add a new task |
| `add <title> --priority high\|medium\|low` | Add with priority (default: medium) |
| `add <title> --due YYYY-MM-DD` | Add with a due date |
| `list` | List all tasks, sorted by priority |
| `list --pending` | Show only incomplete tasks |
| `list --search <text>` | Filter tasks by keyword (case-insensitive) |
| `edit <id> <title>` | Update a task's description |
| `done <id>` | Mark a task as complete |
| `delete <id>` | Delete a task |

### Output formatting

- Overdue tasks are highlighted in **red**
- Completed tasks are shown in **green**
- Tasks are sorted by priority: high → medium → low

### Example session

```
$ todo add "Buy milk"
Added task #1: Buy milk

$ todo add "Fix critical bug" --priority high --due 2026-06-10
Added task #2: Fix critical bug

$ todo add "Read book" --priority low
Added task #3: Read book

$ todo list
[ ] #2  Fix critical bug  [high]  due:2026-06-10
[ ] #1  Buy milk  [medium]
[ ] #3  Read book  [low]

$ todo done 1
Marked task #1 as done.

$ todo edit 3 "Read two books"
Updated task #3: Read two books

$ todo list --pending
[ ] #2  Fix critical bug  [high]  due:2026-06-10
[ ] #3  Read two books  [low]

$ todo delete 2
Deleted task #2.
```

## Storage

Tasks are saved to `~/.todoman.json` — plain JSON, human-readable.

## Running tests

```bash
python3 -m unittest discover -s tests -v
```
