# unit tests for tasks api
import json
import pytest
from app import create_app
from app.database import reset_memory_db


@pytest.fixture(autouse=True)
def clean_db():
    # reset db before each test
    reset_memory_db()
    yield
    reset_memory_db()


@pytest.fixture
def app():
    # test app with memory db
    app = create_app(testing=True)
    yield app


@pytest.fixture
def client(app):
    # flask test client
    return app.test_client()


@pytest.fixture
def sample_task(client):
    # helper to make a task for tests
    response = client.post(
        "/tasks",
        json={"title": "Sample Task", "description": "A test task"},
    )
    return json.loads(response.data)["task"]




class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contains_status(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    def test_health_contains_uptime(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))




class TestMetricsEndpoint:

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        response = client.get("/metrics")
        assert "text/plain" in response.content_type

    def test_metrics_contains_uptime(self, client):
        response = client.get("/metrics")
        text = response.data.decode("utf-8")
        assert "app_uptime_seconds" in text




class TestGetTasks:

    def test_get_tasks_empty(self, client):
        response = client.get("/tasks")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["tasks"] == []
        assert data["count"] == 0

    def test_get_tasks_with_data(self, client, sample_task):
        response = client.get("/tasks")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["count"] == 1
        assert data["tasks"][0]["title"] == "Sample Task"

    def test_get_single_task(self, client, sample_task):
        task_id = sample_task["id"]
        response = client.get(f"/tasks/{task_id}")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["task"]["id"] == task_id

    def test_get_nonexistent_task(self, client):
        response = client.get("/tasks/9999")
        assert response.status_code == 404




class TestCreateTask:

    def test_create_task_valid(self, client):
        response = client.post(
            "/tasks",
            json={"title": "New Task", "description": "Description"},
        )
        data = json.loads(response.data)
        assert response.status_code == 201
        assert data["task"]["title"] == "New Task"
        assert data["task"]["status"] == "pending"

    def test_create_task_no_title(self, client):
        response = client.post("/tasks", json={"description": "No title"})
        assert response.status_code == 400

    def test_create_task_empty_body(self, client):
        response = client.post(
            "/tasks",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_task_with_priority(self, client):
        response = client.post(
            "/tasks",
            json={"title": "Urgent", "priority": "critical"},
        )
        data = json.loads(response.data)
        assert response.status_code == 201
        assert data["task"]["priority"] == "critical"

    def test_create_task_invalid_status(self, client):
        response = client.post(
            "/tasks",
            json={"title": "Bad Status", "status": "invalid"},
        )
        assert response.status_code == 400

    def test_create_task_invalid_priority(self, client):
        response = client.post(
            "/tasks",
            json={"title": "Bad Priority", "priority": "ultra"},
        )
        assert response.status_code == 400




class TestUpdateTask:

    def test_update_task_title(self, client, sample_task):
        task_id = sample_task["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated Title"},
        )
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["task"]["title"] == "Updated Title"

    def test_update_task_status(self, client, sample_task):
        task_id = sample_task["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"status": "completed"},
        )
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["task"]["status"] == "completed"

    def test_update_nonexistent_task(self, client):
        response = client.put(
            "/tasks/9999",
            json={"title": "Ghost Task"},
        )
        assert response.status_code == 404

    def test_update_task_invalid_status(self, client, sample_task):
        task_id = sample_task["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"status": "broken"},
        )
        assert response.status_code == 400




class TestDeleteTask:

    def test_delete_task(self, client, sample_task):
        task_id = sample_task["id"]
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 200

        # Verify it's gone
        check = client.get(f"/tasks/{task_id}")
        assert check.status_code == 404

    def test_delete_nonexistent_task(self, client):
        response = client.delete("/tasks/9999")
        assert response.status_code == 404
