# Task Manager - DevOps Pipeline

A Python Flask REST API with a complete CI/CD pipeline using Jenkins, demonstrating all 7 stages of a DevOps workflow.

## Project Overview

Task Manager is a RESTful API built with Flask and SQLite that provides full CRUD operations for managing tasks. The project includes a comprehensive Jenkins pipeline with automated build, test, code quality, security scanning, deployment, release, and monitoring stages.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Application | Python 3.11 / Flask 2.3.3 |
| Database | SQLite |
| Containerisation | Docker / Docker Compose |
| CI/CD | Jenkins (Declarative Pipeline) |
| Testing | pytest + pytest-cov |
| Code Quality | flake8 + SonarQube |
| Security | Bandit (SAST) + Trivy (Container) |
| Monitoring | Prometheus |
| Production Server | Gunicorn |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | List all tasks (supports `?status=` and `?priority=` filters) |
| GET | `/tasks/<id>` | Get a specific task |
| POST | `/tasks` | Create a new task |
| PUT | `/tasks/<id>` | Update an existing task |
| DELETE | `/tasks/<id>` | Delete a task |
| GET | `/health` | Application health check |
| GET | `/metrics` | Prometheus-compatible metrics |

## Pipeline Stages

1. **Build** - Install dependencies and build Docker image with version tagging
2. **Test** - Run unit and integration tests with coverage reporting
3. **Code Quality** - flake8 linting + SonarQube analysis with quality gates
4. **Security** - Bandit SAST scan + Trivy container image scan
5. **Deploy** - Automated staging deployment with health checks and smoke tests
6. **Release** - Production deployment with versioned Docker + Git tags
7. **Monitoring** - Prometheus metrics verification and monitoring report

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
python run.py
```

### Docker
```bash
docker build -t taskmanager:latest .
docker run -p 5000:5000 taskmanager:latest
```

### Full Stack (App + Prometheus)
```bash
docker-compose up -d
```

## Project Structure

```
taskmanager/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # API endpoints + health + metrics
│   ├── models.py            # Task model with CRUD operations
│   └── database.py          # SQLite connection management
├── tests/
│   ├── test_unit.py         # 25 unit tests
│   └── test_integration.py  # 8 integration tests
├── prometheus/
│   └── prometheus.yml       # Prometheus scrape configuration
├── screenshots/             # Jenkins pipeline screenshots
├── Dockerfile               # Production container image
├── docker-compose.yml       # Staging environment
├── docker-compose.prod.yml  # Production environment
├── Jenkinsfile              # 7-stage CI/CD pipeline
├── requirements.txt         # Pinned Python dependencies
├── sonar-project.properties # SonarQube configuration
├── .flake8                  # Linting rules
├── .bandit                  # Security scan configuration
└── run.py                   # Application entry point
```

## Author

SIT223/SIT753 - Professional Practice in IT
Task 7.3HD - DevOps Pipeline with Jenkins
