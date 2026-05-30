# SEO Audit System

## Overview

Async SEO Audit System is a backend service for managing SEO audits at scale. Users can create projects, submit URLs for analysis, process audits asynchronously using Celery + Redis, and view SEO insights through APIs.

The system provides:

* JWT Authentication
* Project Management APIs
* URL Submission APIs
* Asynchronous Background Processing
* SEO Scraping Logic
* Dashboard Metrics
* CSV Bulk Upload
* Dockerized Deployment
* Swagger API Documentation

---

# Tech Stack

| Layer            | Technology                       |
| ---------------- | -------------------------------- |
| Language         | Python 3.13                      |
| Framework        | Django 6 + Django REST Framework |
| Database         | PostgreSQL                       |
| Queue            | Celery                           |
| Broker           | Redis                            |
| Documentation    | drf-spectacular Swagger          |
| Containerization | Docker + Docker Compose          |
| Scraping         | requests + BeautifulSoup         |
| Authentication   | JWT (SimpleJWT)                  |

---

# Features

## Authentication

Supports JWT authentication:

* User Registration
* Login
* Refresh Tokens
* Protected APIs

Users only access their own resources.

---

## Project Management

Supports:

* Create Project
* List Projects
* Update Project
* Delete Project

Project fields:

* name
* domain
* created_at

---

## Audit Processing

Users can:

* Submit URLs
* Queue audits asynchronously
* Fetch results later

Audit stores:

* URL
* Status
* Page Title
* Meta Description
* H1 Count
* Word Count
* SEO Score
* Errors

---

## Dashboard Metrics

Dashboard provides:

* Total audited URLs
* Failed audits
* Average SEO score
* Missing titles
* Missing meta descriptions

---

## CSV Upload

Supports:

* CSV upload
* Invalid row skipping
* Duplicate detection
* URL validation
* Bulk queueing

---

## Security

Implemented:

* JWT Authentication
* User-level isolation
* Project ownership checks
* Audit ownership checks

---

# Architecture

```text
User Request
      ↓
DRF API Layer
      ↓
JWT Authentication + Permission Validation
      ↓
URL Validation / CSV Parsing
      ↓
Create Audit Records in Database (Pending State)
      ↓
Database Transaction Commit
      ↓
Queue Celery Tasks
      ↓
Redis Broker
      ↓
Celery Worker
      ↓
SEO Scraper Service
      ↓
Extract SEO Metrics
(Title, Meta Description, H1 Count, Word Count)
      ↓
Generate SEO Score
      ↓
Update Audit Status
(Completed / Failed)
      ↓
Store Final Results in Database
      ↓
Results API / Dashboard API
```

## Processing Flow

1. User submits URLs or uploads CSV.
2. Request passes authentication and ownership checks.
3. URLs are validated and duplicate entries are prevented.
4. Audit records are created in database with pending status.
5. After successful transaction commit, Celery tasks are queued.
6. Redis acts as broker between API layer and Celery workers.
7. Worker processes each URL asynchronously.
8. SEO data is extracted and SEO score is calculated.
9. Audit record gets updated as completed or failed.
10. Users fetch results using dashboard and audit APIs.

This design ensures reliability because tasks are only queued after database records are successfully stored.

---

# Installation (Local Setup)

## Clone Repository

```bash
git clone https://github.com/AnubhavBangari3/SEOauditsystem.git
cd SEOauditsystem
```

## Create Virtual Environment

```bash
python -m venv env
```

Windows:

```bash
env\Scripts\activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Run Migrations

```bash
python manage.py migrate
```

## Create Superuser

```bash
python manage.py createsuperuser
```

---

# Redis Setup

This project uses Redis as the Celery broker. Redis must be running before Celery tasks can be queued and processed.

## Check Existing Redis Container

Before creating a new Redis container, check if one already exists:

```bash
docker ps -a
```

If a container named `seo-redis` already exists, start it:

```bash
docker start seo-redis
```

Verify Redis is running:

```bash
docker ps
```

Expected output should contain:

```text
CONTAINER ID   IMAGE            STATUS      PORTS                    NAMES
xxxx           redis:7-alpine   Up ...      0.0.0.0:6379->6379/tcp   seo-redis
```

## Create Redis Container First Time

If Redis container does not exist, create it:

```bash
docker run --name seo-redis -p 6379:6379 -d redis:7-alpine
```

What this does:

```text
--name seo-redis   -> container name
-p 6379:6379       -> expose Redis port
-d                 -> run in background
redis:7-alpine     -> lightweight Redis image
```

## Fix Redis Container Conflict / Corrupted Container

If this error appears:

```text
docker: Error response from daemon: Conflict.
The container name "/seo-redis" is already in use.
```

Then stop and remove the old container:

```bash
docker stop seo-redis
docker rm seo-redis
```

Then recreate it:

```bash
docker run --name seo-redis -p 6379:6379 -d redis:7-alpine
```

## Verify Redis Works

```bash
docker exec -it seo-redis redis-cli ping
```

Expected output:

```text
PONG
```

## Why `python manage.py runserver` May Fail Without Redis

Some APIs queue Celery background jobs. If Redis is not running, the Django server or audit submission flow may fail with Redis/Celery connection errors.

Common errors:

```text
Connection refused
Redis connection error
Celery broker unavailable
```

So start Redis before running Django and Celery.

---

# Run Project Locally

Use 3 separate terminals.

## Terminal 1: Start Redis

If container already exists:

```bash
docker start seo-redis
```

If container is broken or Redis is not working:

```bash
docker stop seo-redis
docker rm seo-redis
docker run --name seo-redis -p 6379:6379 -d redis:7-alpine
```

Verify:

```bash
docker exec -it seo-redis redis-cli ping
```

Expected:

```text
PONG
```

## Terminal 2: Start Django Server

```bash
python manage.py runserver
```

## Terminal 3: Start Celery Worker

Windows:

```bash
celery -A config worker -l info --pool=solo
```

---

# Celery Setup

Run worker:

```bash
celery -A config worker -l info --pool=solo
```

`--pool=solo` is recommended on Windows to avoid multiprocessing issues.

---

# Docker Setup

This project also supports Docker Compose.

## Start Full Docker Setup

```bash
docker-compose up --build
```

## Start Full Docker Setup in Background

```bash
docker-compose up -d --build
```

## Stop Docker Services

```bash
docker-compose down
```

## View Logs

```bash
docker-compose logs -f
```

## Rebuild Cleanly

```bash
docker-compose down
docker-compose up --build
```

Expected output:

```text
web service running
db service running
redis service running
celery service running
```

---

# API Documentation

Swagger:

```text
/api/docs/
```

Schema:

```text
/api/schema/
```

Redoc:

```text
/api/redoc/
```

---

# API Endpoints

## Authentication

| Method | Endpoint            |
| ------ | ------------------- |
| POST   | /api/auth/register/ |
| POST   | /api/auth/login/    |
| POST   | /api/auth/refresh/  |

## Projects

| Method | Endpoint            |
| ------ | ------------------- |
| GET    | /api/projects/      |
| POST   | /api/projects/      |
| PUT    | /api/projects/{id}/ |
| DELETE | /api/projects/{id}/ |

## Audits

| Method | Endpoint                             |
| ------ | ------------------------------------ |
| POST   | /api/audits/submit/{project_id}/     |
| POST   | /api/audits/upload-csv/{project_id}/ |
| GET    | /api/audits/                         |
| GET    | /api/audits/dashboard/               |

---

# Filtering

Supports:

```text
?status=
?min_score=
?max_score=
?project=
?search=
?ordering=
```

Examples:

```text
/api/audits/?status=completed
/api/audits/?min_score=50
/api/audits/?search=google
```

---

# Pagination

Default:

```text
10 results/page
```

Supports:

```text
?page=
&page_size=
```

---

# SEO Processing Logic

SEO score generated using:

* Title presence
* Meta description presence
* H1 tags
* Word count

Scoring uses lightweight mock logic for evaluation.

---

# Testing

Run tests:

```bash
python manage.py test
```

Current status:

```text
18 tests passed
```

Coverage includes:

* Authentication
* Projects
* Permissions
* URL Submission
* Dashboard
* CSV Upload
* Celery Queueing

---

# Folder Structure

```text
apps/
├── accounts/
├── projects/
├── audits/

common/
config/
media/
```

---

# Assumptions

* Simple SEO scoring is sufficient
* No distributed crawling required
* Single worker environment
* URLs processed independently

---

# Tradeoffs

* Mock scoring instead of production SEO engine
* Simple scraper instead of crawler
* Celery task per URL
* Focused on backend architecture over crawler complexity

---

# Future Improvements

* Redis caching
* Celery Beat re-audits
* Async scraping with aiohttp
* Rate limiting
* AI SEO recommendations
* WebSocket progress updates

---

# Submission Checklist

* Dockerized
* Async Processing
* JWT Auth
* PostgreSQL
* Redis
* Celery
* Swagger Docs
* CSV Upload
* Tests Passing
* README Added
* .env.example Included
