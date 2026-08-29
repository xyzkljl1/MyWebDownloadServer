# coding: utf-8
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_download_task.py <queue_id>")
        return 2

    try:
        task_id = int(sys.argv[1])
    except ValueError:
        print("queue_id must be an integer")
        return 2

    import database
    import my_server

    task = database.GetTask(task_id)
    if task is None:
        print("Task not found:", task_id)
        return 1

    success, msg = my_server.ProcessTask(*task, update_queue=False)
    if success:
        print("Debug task success:", task_id)
        return 0

    print("Debug task failed:", task_id, msg)
    return 1


if __name__ == '__main__':
    sys.exit(main())
