"""Unit tests for the Task Manager application.

Tests cover all CRUD operations, input validation, edge cases,
and the health/metrics endpoints.
"""
import json
import pytest
from app import create_app
from app.database import reset_memory_db


@pytest.fixture(autouse=True)
def clean_db():
    """Reset the in-memory database before each test."""
    reset_memory_db()
    yield
    reset_memory_db()


@pytest.fixture
def app():
    """Create a test application with an in-memory database."""
    app = create_app(testing=True)
    yield app


@pytest.fixture
def client(app):
    """Create a test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def sample_task(client):
    """Create and return a sample task for tests that need one."""
    response = client.post(
        "/tasks",
        json={"title": "Sample Task", "description": "A test task"},
    )
    return json.loads(response.data)["task"]


# ── Health Endpoint Tests ───────────────────────────────────────

class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Health check should return a 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contains_status(self, client):
        """Health response should include a 'healthy' status field."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    def test_health_contains_uptime(self, client):
        """Health response should contain uptime in seconds."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))


# ── Metrics Endpoint Tests ──────────────────────────────────────

class TestMetricsEndpoint:
    """Tests for the /metrics endpoint."""

    def test_metrics_returns_200(self, client):
        """Metrics endpoint should return 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Metrics should be returned as plain text."""
        response = client.get("/metrics")
        assert "text/plain" in response.content_type

    def test_metrics_contains_uptime(self, client):
        """Metrics output should contain the uptime gauge."""
        response = client.get("/metrics")
        text = response.data.decode("utf-8")
        assert "app_uptime_seconds" in text


# ── GET /tasks Tests ────────────────────────────────────────────

class TestGetTasks:
    """Tests for retrieving tasks."""

    def test_get_tasks_empty(self, client):
        """GET /tasks on empty database should return empty list."""
        response = client.get("/tasks")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["tasks"] == []
        assert data["count"] == 0

    def test_get_tasks_with_data(self, client, sample_task):
        """GET /tasks should return existing tasks."""
        response = client.get("/tasks")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Sample Task"

    def test_get_single_task(self, client, sample_task):
        """GET /tasks/<id> should return the correct task."""
        task_id = sample_task["id"]
        response = client.get(f"/tasks/{task_id}")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["task"]["id"] == task_id

    def test_get_nonexistent_task(self, client):
        """GET /tasks/<id> with invalid ID should return 404."""
        response = client.get("/tasks/9999")
        assert response.status_code == 404


# ── POST /tasks Tests ───────────────────────────────────────────

class TestCreateTask:
    """Tests for creating tasks."""

    def test_create_task_valid(self, client):
        """POST /tasks with valid data should create a task."""
        response = client.post(
            "/tasks",
            json={"title": "New Task", "description": "Description"},
        )
        data = json.loads(response.data)
        assert response.status_code == 201
        assert data["task"]["title"] == "New Task"
        assert data["task"]["status"] == "pending"

    def test_create_task_no_title(self, client):
        """POST /tasks without title should return 400."""
        response = client.post("/tasks", json={"description": "No title"})
        assert response.status_code == 400

    def test_create_task_empty_body(self, client):
        """POST /tasks with empty body should return 400."""
        response = client.post(
            "/tasks",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_task_with_priority(self, client):
        """POST /tasks with custom priority should store it."""
        response = client.post(
            "/tasks",
            json={"title": "Urgent", "priority": "critical"},
        )
        data = json.loads(response.data)
        assert response.status_code == 201
        assert data["task"]["priority"] == "critical"

    def test_create_task_invalid_status(self, client):
        """POST /tasks with invalid status should return 400."""
        response = client.post(
            "/tasks",
            json={"title": "Bad Status", "status": "invalid"},
        )
        assert response.status_code == 400

    def test_create_task_invalid_priority(self, client):
        """POST /tasks with invalid priority should return 400."""
        response = client.post(
            "/tasks",
            json={"title": "Bad Priority", "priority": "ultra"},
        )
        assert response.status_code == 400


# ── PUT /tasks Tests ────────────────────────────────────────────

class TestUpdateTask:
    """Tests for updating tasks."""

    def test_update_task_title(self, client, sample_task):
        """PUT /tasks/<id> should update the title."""
        task_id = sample_task["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated Title"},
        )
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["task"]["title"] == "Updated Title"

    def test_update_task_status(self, client, sample_task):
        """PUT /tasks/<id> should update the status."""
        task_id = sample_task["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"status": "completed"},
        )
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["task"]["status"] == "completed"

    def test_update_nonexistent_task(self, client):
        """PUT /tasks/<id> with invalid ID should return 404."""
        response = client.put(
            "/tasks/9999",
            json={"title": "Ghost Task"},
        )
        assert response.status_code == 404

    def test_update_task_invalid_status(self, client, sample_task):
        """PUT /tasks/<id> with invalid status should return 400."""
        task_id = sample_task["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"status": "broken"},
        )
        assert response.status_code == 400


# ── DELETE /tasks Tests ─────────────────────────────────────────

class TestDeleteTask:
    """Tests for deleting tasks."""

    def test_delete_task(self, client, sample_task):
        """DELETE /tasks/<id> should remove the task."""
        task_id = sample_task["id"]
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 200

        # Verify it's gone
        check = client.get(f"/tasks/{task_id}")
        assert check.status_code == 404

    def test_delete_nonexistent_task(self, client):
        """DELETE /tasks/<id> with invalid ID should return 404."""
        response = client.delete("/tasks/9999")
        assert response.status_code == 404
