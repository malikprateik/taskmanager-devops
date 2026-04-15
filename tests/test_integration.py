"""Integration tests for the Task Manager application.

These tests verify end-to-end workflows that span multiple
endpoints, simulating real user interactions with the API.
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


class TestTaskWorkflow:
    """Integration tests for complete task lifecycle workflows."""

    def test_full_crud_lifecycle(self, client):
        """Test the complete lifecycle: create, read, update, delete."""
        # Create
        create_resp = client.post(
            "/tasks",
            json={
                "title": "Integration Test Task",
                "description": "Full lifecycle test",
                "priority": "high",
            },
        )
        assert create_resp.status_code == 201
        task = json.loads(create_resp.data)["task"]
        task_id = task["id"]
        assert task["title"] == "Integration Test Task"
        assert task["priority"] == "high"
        assert task["status"] == "pending"

        # Read back
        get_resp = client.get(f"/tasks/{task_id}")
        assert get_resp.status_code == 200
        read_task = json.loads(get_resp.data)["task"]
        assert read_task["title"] == "Integration Test Task"

        # Update
        update_resp = client.put(
            f"/tasks/{task_id}",
            json={"status": "in_progress", "title": "Updated Task"},
        )
        assert update_resp.status_code == 200
        updated = json.loads(update_resp.data)["task"]
        assert updated["status"] == "in_progress"
        assert updated["title"] == "Updated Task"

        # Delete
        delete_resp = client.delete(f"/tasks/{task_id}")
        assert delete_resp.status_code == 200

        # Verify gone
        verify_resp = client.get(f"/tasks/{task_id}")
        assert verify_resp.status_code == 404

    def test_multiple_tasks_ordering(self, client):
        """Verify that multiple tasks are returned in order."""
        titles = ["First Task", "Second Task", "Third Task"]
        for title in titles:
            resp = client.post("/tasks", json={"title": title})
            assert resp.status_code == 201

        list_resp = client.get("/tasks")
        data = json.loads(list_resp.data)
        assert data["count"] == 3

        # Tasks should be ordered by created_at DESC
        returned_titles = [t["title"] for t in data["tasks"]]
        assert returned_titles == list(reversed(titles))

    def test_filter_tasks_by_status(self, client):
        """Verify filtering tasks by status query parameter."""
        # Create tasks with different statuses
        client.post(
            "/tasks",
            json={"title": "Pending Task", "status": "pending"},
        )
        client.post(
            "/tasks",
            json={"title": "Completed Task", "status": "completed"},
        )
        client.post(
            "/tasks",
            json={"title": "Another Pending", "status": "pending"},
        )

        # Filter for pending
        resp = client.get("/tasks?status=pending")
        data = json.loads(resp.data)
        assert data["count"] == 2
        for task in data["tasks"]:
            assert task["status"] == "pending"

        # Filter for completed
        resp = client.get("/tasks?status=completed")
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Completed Task"

    def test_filter_tasks_by_priority(self, client):
        """Verify filtering tasks by priority query parameter."""
        client.post(
            "/tasks",
            json={"title": "Low Task", "priority": "low"},
        )
        client.post(
            "/tasks",
            json={"title": "Critical Task", "priority": "critical"},
        )

        resp = client.get("/tasks?priority=critical")
        data = json.loads(resp.data)
        assert data["count"] == 1
        assert data["tasks"][0]["priority"] == "critical"

    def test_health_reflects_running_state(self, client):
        """Health endpoint should reflect a running app with metrics."""
        # Hit some endpoints to generate metrics
        client.post("/tasks", json={"title": "Metrics Task"})
        client.get("/tasks")

        health_resp = client.get("/health")
        data = json.loads(health_resp.data)
        assert data["status"] == "healthy"
        assert data["uptime_seconds"] >= 0

    def test_metrics_reflect_activity(self, client):
        """Metrics endpoint should reflect request counts."""
        # Generate some traffic
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        client.get("/tasks")
        client.get("/tasks")
        client.get("/tasks")

        metrics_resp = client.get("/metrics")
        text = metrics_resp.data.decode("utf-8")

        # Should have task count metric
        assert "app_tasks_total" in text
        # Should have request counter metric
        assert "app_requests_total" in text
        # Should have endpoint hit tracking
        assert "app_endpoint_hits" in text

    def test_error_handling_consistency(self, client):
        """All error responses should have consistent JSON structure."""
        # 404 on GET
        resp1 = client.get("/tasks/999")
        assert resp1.status_code == 404
        assert "error" in json.loads(resp1.data)

        # 404 on PUT
        resp2 = client.put("/tasks/999", json={"title": "X"})
        assert resp2.status_code == 404
        assert "error" in json.loads(resp2.data)

        # 404 on DELETE
        resp3 = client.delete("/tasks/999")
        assert resp3.status_code == 404
        assert "error" in json.loads(resp3.data)

        # 400 on bad POST
        resp4 = client.post("/tasks", json={})
        assert resp4.status_code == 400
        assert "error" in json.loads(resp4.data)
