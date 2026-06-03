import argparse

from todo import storage
from todo.models import Task


def cmd_add(args: argparse.Namespace) -> None:
    tasks = storage.load()
    task = Task(id=max((t.id for t in tasks), default=0) + 1, title=args.title)
    tasks.append(task)
    storage.save(tasks)
    print(f"Added task #{task.id}: {task.title}")


def cmd_list(args: argparse.Namespace) -> None:
    tasks = storage.load()
    if not tasks:
        print("No tasks yet. Use `todo add <title>` to create one.")
        return
    for t in tasks:
        status = "x" if t.done else " "
        print(f"[{status}] #{t.id}  {t.title}")


def cmd_done(args: argparse.Namespace) -> None:
    tasks = storage.load()
    for t in tasks:
        if t.id == args.id:
            t.done = True
            storage.save(tasks)
            print(f"Marked task #{t.id} as done.")
            return
    print(f"Error: no task with ID {args.id}.")


def cmd_delete(args: argparse.Namespace) -> None:
    print("not yet implemented: delete")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="A minimal command-line to-do manager",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    p_add = sub.add_parser("add", help="Add a new task")
    p_add.add_argument("title", help="Task description")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List all tasks")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="Mark a task as complete")
    p_done.add_argument("id", type=int, help="Task ID")
    p_done.set_defaults(func=cmd_done)

    p_del = sub.add_parser("delete", help="Delete a task")
    p_del.add_argument("id", type=int, help="Task ID")
    p_del.set_defaults(func=cmd_delete)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
