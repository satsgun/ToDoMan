import argparse
import sys
from datetime import date

from todo import storage
from todo.models import Task


def valid_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid date (use YYYY-MM-DD)")
    if parsed < date.today():
        raise argparse.ArgumentTypeError(f"due date cannot be in the past")
    return value


def positive_int(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{value}' is not an integer")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"ID must be a positive integer, got {value}")
    return n


def cmd_add(args: argparse.Namespace) -> None:
    title = args.title.strip()
    if not title:
        sys.exit("Error: task title cannot be blank.")
    tasks = storage.load()
    task = Task(
        id=max((t.id for t in tasks), default=0) + 1,
        title=title,
        priority=args.priority,
        due_date=args.due,
    )
    tasks.append(task)
    storage.save(tasks)
    print(f"Added task #{task.id}: {task.title}")


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_RED = "\033[31m"
_GREEN = "\033[32m"
_RESET = "\033[0m"
_USE_COLOR = sys.stdout.isatty()


def cmd_list(args: argparse.Namespace) -> None:
    tasks = storage.load()
    if not tasks:
        print("No tasks yet. Use `todo add <title>` to create one.")
        return
    if args.pending:
        tasks = [t for t in tasks if not t.done]
    if args.search:
        keyword = args.search.lower()
        tasks = [t for t in tasks if keyword in t.title.lower()]
    if not tasks:
        print("No matching tasks.")
        return
    today = date.today()
    for t in sorted(tasks, key=lambda t: _PRIORITY_ORDER.get(t.priority, 1)):
        status = "x" if t.done else " "
        line = f"[{status}] #{t.id}  {t.title}  [{t.priority}]"
        if t.due_date:
            line += f"  due:{t.due_date}"
        if _USE_COLOR:
            if t.done:
                line = f"{_GREEN}{line}{_RESET}"
            elif t.due_date and date.fromisoformat(t.due_date) < today:
                line = f"{_RED}{line}{_RESET}"
        print(line)


def cmd_done(args: argparse.Namespace) -> None:
    tasks = storage.load()
    for t in tasks:
        if t.id == args.id:
            if t.done:
                print(f"Task #{t.id} is already done.")
                return
            t.done = True
            storage.save(tasks)
            print(f"Marked task #{t.id} as done.")
            return
    sys.exit(f"Error: no task with ID {args.id}.")


def cmd_edit(args: argparse.Namespace) -> None:
    title = args.title.strip()
    if not title:
        sys.exit("Error: task title cannot be blank.")
    tasks = storage.load()
    for t in tasks:
        if t.id == args.id:
            t.title = title
            storage.save(tasks)
            print(f"Updated task #{t.id}: {t.title}")
            return
    sys.exit(f"Error: no task with ID {args.id}.")


def cmd_delete(args: argparse.Namespace) -> None:
    tasks = storage.load()
    remaining = [t for t in tasks if t.id != args.id]
    if len(remaining) == len(tasks):
        sys.exit(f"Error: no task with ID {args.id}.")
    storage.save(remaining)
    print(f"Deleted task #{args.id}.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A minimal command-line to-do manager",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Task description")
    p_add.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Task priority (default: medium)",
    )
    p_add.add_argument(
        "--due",
        type=valid_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="Due date",
    )
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all tasks")
    p_list.add_argument("--pending", action="store_true", help="Show only incomplete tasks")
    p_list.add_argument("--search", metavar="TEXT", default=None, help="Filter by keyword (case-insensitive)")
    p_list.set_defaults(func=cmd_list)

    p_edit = sub.add_parser("edit", help="Edit a task's description")
    p_edit.add_argument("id", type=positive_int, help="Task ID")
    p_edit.add_argument("title", help="New task description")
    p_edit.set_defaults(func=cmd_edit)

    p_done = sub.add_parser("done", help="Mark a task as complete")
    p_done.add_argument("id", type=positive_int, help="Task ID")
    p_done.set_defaults(func=cmd_done)

    p_del = sub.add_parser("delete", help="Delete a task")
    p_del.add_argument("id", type=positive_int, help="Task ID")
    p_del.set_defaults(func=cmd_delete)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
