"""REST API routes for the Task Manager application.

Provides full CRUD operations on tasks plus health and metrics
endpoints required for the DevOps monitoring stage.
"""
import time
import platform
from flask import Blueprint, request, jsonify
from .models import Task

api_bp = Blueprint("api", __name__)

# Track request metrics in memory
_metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_error": 0,
    "start_time": time.time(),
    "endpoint_hits": {},
}


def _track(endpoint, success=True):
    """Record a request for the metrics endpoint."""
    _metrics["requests_total"] += 1
    if success:
        _metrics["requests_success"] += 1
    else:
        _metrics["requests_error"] += 1
    _metrics["endpoint_hits"][endpoint] = (
        _metrics["endpoint_hits"].get(endpoint, 0) + 1
    )


# ── Health & Metrics ────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Return application health status.

    Used by the deploy and monitoring pipeline stages to verify
    the application is running correctly.
    """
    uptime = time.time() - _metrics["start_time"]
    return jsonify({
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "version": "1.0.0",
        "python_version": platform.python_version(),
        "platform": platform.system(),
    }), 200


@api_bp.route("/metrics", methods=["GET"])
def prometheus_metrics():
    """Return Prometheus-compatible metrics in text exposition format.

    This endpoint is scraped by Prometheus for monitoring.
    """
    uptime = time.time() - _metrics["start_time"]

    try:
        task_count = Task.count()
        status_counts = Task.count_by_status()
    except Exception:
        task_count = 0
        status_counts = {}

    lines = [
        "# HELP app_uptime_seconds Application uptime in seconds",
        "# TYPE app_uptime_seconds gauge",
        f"app_uptime_seconds {uptime:.2f}",
        "",
        "# HELP app_requests_total Total number of HTTP requests",
        "# TYPE app_requests_total counter",
        f"app_requests_total {_metrics['requests_total']}",
        "",
        "# HELP app_requests_success Total successful requests",
        "# TYPE app_requests_success counter",
        f"app_requests_success {_metrics['requests_success']}",
        "",
        "# HELP app_requests_error Total failed requests",
        "# TYPE app_requests_error counter",
        f"app_requests_error {_metrics['requests_error']}",
        "",
        "# HELP app_tasks_total Total number of tasks",
        "# TYPE app_tasks_total gauge",
        f"app_tasks_total {task_count}",
        "",
        "# HELP app_tasks_by_status Number of tasks by status",
        "# TYPE app_tasks_by_status gauge",
    ]

    for status, count in status_counts.items():
        lines.append(
            f'app_tasks_by_status{{status="{status}"}} {count}'
        )

    for endpoint, hits in _metrics["endpoint_hits"].items():
        lines.append(
            f'app_endpoint_hits{{endpoint="{endpoint}"}} {hits}'
        )

    return "\n".join(lines) + "\n", 200, {
        "Content-Type": "text/plain; charset=utf-8"
    }


# ── CRUD Endpoints ──────────────────────────────────────────────

@api_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """Retrieve all tasks, optionally filtered by status or priority."""
    _track("GET /tasks")

    tasks = Task.get_all()
    task_list = [t.to_dict() for t in tasks]

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")

    if status_filter:
        task_list = [
            t for t in task_list if t["status"] == status_filter
        ]
    if priority_filter:
        task_list = [
            t for t in task_list if t["priority"] == priority_filter
        ]

    return jsonify({
        "tasks": task_list,
        "count": len(task_list),
    }), 200


@api_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """Retrieve a single task by its ID."""
    _track(f"GET /tasks/{task_id}")

    task = Task.get_by_id(task_id)
    if task is None:
        _track(f"GET /tasks/{task_id}", success=False)
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"task": task.to_dict()}), 200


@api_bp.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task.

    Expects JSON body with at least a "title" field.
    Optional: description, status, priority.
    """
    _track("POST /tasks")

    data = request.get_json()
    if not data:
        _track("POST /tasks", success=False)
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title")
    if not title:
        _track("POST /tasks", success=False)
        return jsonify({"error": "Title is required"}), 400

    try:
        task = Task.create(
            title=title,
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", "medium"),
        )
    except ValueError as e:
        _track("POST /tasks", success=False)
        return jsonify({"error": str(e)}), 400

    return jsonify({"task": task.to_dict()}), 201


@api_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    """Update an existing task.

    Accepts any combination of: title, description, status, priority.
    """
    _track(f"PUT /tasks/{task_id}")

    data = request.get_json()
    if not data:
        _track(f"PUT /tasks/{task_id}", success=False)
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        task = Task.update(task_id, **data)
    except ValueError as e:
        _track(f"PUT /tasks/{task_id}", success=False)
        return jsonify({"error": str(e)}), 400

    if task is None:
        _track(f"PUT /tasks/{task_id}", success=False)
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"task": task.to_dict()}), 200


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task by its ID."""
    _track(f"DELETE /tasks/{task_id}")

    deleted = Task.delete(task_id)
    if not deleted:
        _track(f"DELETE /tasks/{task_id}", success=False)
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": f"Task {task_id} deleted"}), 200
