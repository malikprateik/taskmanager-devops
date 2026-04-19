# task model for db operations
from .database import get_db


VALID_STATUSES = ("pending", "in_progress", "completed", "cancelled")
VALID_PRIORITIES = ("low", "medium", "high", "critical")


class Task:
    # stores a single task from the db

    def __init__(self, id, title, description, status,
                 priority, created_at, updated_at):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        # turn into json dict
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }

    @staticmethod
    def _row_to_task(row):
        # row -> task object
        if row is None:
            return None
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def get_all():
        # fetch all tasks
        db = get_db()
        rows = db.execute(
            "SELECT * FROM tasks ORDER BY id DESC"
        ).fetchall()
        return [Task._row_to_task(r) for r in rows]

    @staticmethod
    def get_by_id(task_id):
        # get one task by id
        db = get_db()
        row = db.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return Task._row_to_task(row)

    @staticmethod
    def create(title, description="", status="pending",
               priority="medium"):
        # add a new task to db
        if not title or not title.strip():
            raise ValueError("Title is required and cannot be empty")
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of: {VALID_STATUSES}"
            )
        if priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority. Must be one of: {VALID_PRIORITIES}"
            )

        db = get_db()
        cursor = db.execute(
            """INSERT INTO tasks (title, description, status, priority)
               VALUES (?, ?, ?, ?)""",
            (title.strip(), description.strip(), status, priority),
        )
        db.commit()
        return Task.get_by_id(cursor.lastrowid)

    @staticmethod
    def update(task_id, **kwargs):
        # update fields on a task
        task = Task.get_by_id(task_id)
        if task is None:
            return None

        allowed_fields = {"title", "description", "status", "priority"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return task

        if "status" in updates and updates["status"] not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of: {VALID_STATUSES}"
            )
        if "priority" in updates and updates["priority"] not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority. Must be one of: {VALID_PRIORITIES}"
            )
        if "title" in updates:
            if not updates["title"] or not updates["title"].strip():
                raise ValueError("Title cannot be empty")
            updates["title"] = updates["title"].strip()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        values = list(updates.values()) + [task_id]

        db = get_db()
        db.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?", values
        )
        db.commit()
        return Task.get_by_id(task_id)

    @staticmethod
    def delete(task_id):
        # remove a task
        task = Task.get_by_id(task_id)
        if task is None:
            return False
        db = get_db()
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        return True

    @staticmethod
    def count():
        # count all tasks
        db = get_db()
        row = db.execute("SELECT COUNT(*) as cnt FROM tasks").fetchone()
        return row["cnt"]

    @staticmethod
    def count_by_status():
        # group count by status
        db = get_db()
        rows = db.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        return {row["status"]: row["cnt"] for row in rows}
