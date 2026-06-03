# todoman

A minimal command-line to-do manager.

## Requirements

- Python 3.10+
- No external dependencies

## Installation

```bash
git clone <repo-url>
cd TodoMan_prj1
```

## Usage

```bash
python3 main.py <command>
# or
python3 -m todo <command>
```

### Commands

| Command | Description |
|---|---|
| `add <title>` | Add a new task |
| `list` | List all tasks |
| `done <id>` | Mark a task as complete |
| `delete <id>` | Delete a task |

### Example session

```
$ python3 main.py add "Buy milk"
Added task #1: Buy milk

$ python3 main.py add "Write tests"
Added task #2: Write tests

$ python3 main.py list
[ ] #1  Buy milk
[ ] #2  Write tests

$ python3 main.py done 1
Marked task #1 as done.

$ python3 main.py list
[x] #1  Buy milk
[ ] #2  Write tests

$ python3 main.py delete 2
Deleted task #2.

$ python3 main.py list
[x] #1  Buy milk
```

## Storage

Tasks are saved to `~/.todoman.json` — plain JSON, human-readable.

## Running tests

```bash
python3 -m unittest discover -s tests -v
```
