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
* Retry and Failure Handling
* Duplicate URL Protection
* Paginated and Filterable Audit Results

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
| Filtering        | django-filter                    |
| Environment      | python-dotenv                    |

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
* Error Message
* Created Date
* Updated Date

Audit statuses:

* pending
* completed
* failed

---

## Dashboard Metrics

Dashboard provides:

* Total audited URLs
* Failed audits
* Average SEO score
* Missing titles
* Missing meta descriptions

Dashboard can also be filtered by project.

---

## CSV Upload

Supports:

* CSV upload
* Invalid row skipping
* Empty row skipping
* Duplicate detection
* URL validation
* UTF-8 CSV parsing
* Bulk queueing
* Response summary with invalid and duplicate row details

---

## Duplicate Protection Strategy

Duplicate URLs are prevented using multiple protection layers:

* Request-level duplicate validation
* CSV duplicate detection
* Existing project URL validation
* Database-level unique constraint enforcement

Database uniqueness:

```text
(project, url)
```

This prevents accidental duplicate audits within the same project.

---

## Security

Implemented:

* JWT Authentication
* User-level isolation
* Project ownership checks
* Audit ownership checks
* Authenticated-only APIs
* Users can only view their own projects and audit results

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
Duplicate Validation Layer
      ↓
Create Audit Records in Database (Pending State)
      ↓
Database Transaction Commit
      ↓
Queue Celery Tasks using transaction.on_commit()
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
3. URLs are validated.
4. Duplicate entries are prevented.
5. Audit records are created in database with pending status.
6. Database transaction completes successfully.
7. Celery tasks are queued only after successful database commit using `transaction.on_commit()`.
8. Redis acts as broker between API layer and Celery workers.
9. Celery worker processes each URL asynchronously.
10. SEO data is extracted from the webpage.
11. SEO score is calculated.
12. Audit record gets updated as completed or failed.
13. Users fetch results using dashboard and audit APIs.

This design ensures reliability because tasks are only queued after database records are successfully stored. It also prevents orphan Celery jobs and inconsistent audit states.

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
DEBUG=True
SECRET_KEY=your-secret-key

DB_NAME=seo_audit_db
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5433

REDIS_HOST=localhost
REDIS_PORT=6380

ALLOWED_HOSTS=127.0.0.1,localhost,web

CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/1
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

`--pool=solo` is recommended on Windows to avoid multiprocessing issues.

---

# Celery Setup

Run worker:

```bash
celery -A config worker -l info --pool=solo
```

Run Celery test task if needed from Django shell:

```bash
python manage.py shell
```

```python
from apps.audits.tasks import test_celery_task
test_celery_task.delay()
```

---

# Docker Setup

This project also supports Docker Compose.

## Start Full Docker Setup

```bash
docker-compose up --build
```

## Start Full Docker Setup After Initial Build

```bash
docker-compose up
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

Expected services:

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

| Method | Endpoint            | Description          |
| ------ | ------------------- | -------------------- |
| POST   | /api/auth/register/ | Register new user    |
| POST   | /api/auth/login/    | Login and get tokens |
| POST   | /api/auth/refresh/  | Refresh access token |

## Projects

| Method | Endpoint            | Description        |
| ------ | ------------------- | ------------------ |
| GET    | /api/projects/      | List projects      |
| POST   | /api/projects/      | Create project     |
| GET    | /api/projects/{id}/ | Retrieve project   |
| PUT    | /api/projects/{id}/ | Update project     |
| PATCH  | /api/projects/{id}/ | Partial update     |
| DELETE | /api/projects/{id}/ | Delete project     |

## Audits

| Method | Endpoint                             | Description                    |
| ------ | ------------------------------------ | ------------------------------ |
| POST   | /api/audits/submit/{project_id}/     | Submit URLs for audit          |
| POST   | /api/audits/upload-csv/{project_id}/ | Upload CSV containing URLs     |
| GET    | /api/audits/                         | Paginated audit results        |
| GET    | /api/audits/{id}/                    | Retrieve audit details         |
| GET    | /api/audits/dashboard/               | Dashboard metrics              |

---

# Example URL Submission Request

Endpoint:

```text
POST /api/audits/submit/2/
```

Request:

```json
{
  "urls": [
    "https://example.com",
    "https://google.com"
  ]
}
```

Example Response:

```json
{
  "message": "URLs submitted successfully and audit jobs queued.",
  "count": 2,
  "data": []
}
```

---

# Example CSV Upload Request

Endpoint:

```text
POST /api/audits/upload-csv/2/
```

Request type:

```text
multipart/form-data
```

Field:

```text
file=<urls.csv>
```

CSV example:

```csv
url
https://example.com
https://google.com
```

The API handles invalid rows, duplicate URLs, empty rows, and valid queued URLs.

---

# Audit Results API

The audit results API provides paginated audit records for the authenticated user.

Supports:

* Pagination
* Search by URL
* Filter by audit status
* Filter by SEO score range
* Filter by project
* Ordering by created date, updated date, SEO score, and word count

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
/api/audits/?max_score=90
/api/audits/?search=google
/api/audits/?project=2
/api/audits/?ordering=-seo_score
/api/audits/?ordering=created_at
/api/audits/?status=completed&min_score=50
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

Examples:

```text
/api/audits/?page=1
/api/audits/?page=2&page_size=10
```

---

# SEO Processing Logic

For each URL, the system fetches the webpage and extracts:

* Page title
* Meta description
* H1 count
* Word count

SEO score is generated using lightweight scoring rules:

| Metric | Score |
| ------ | ----- |
| Title present | +25 |
| Meta description present | +25 |
| At least one H1 tag | +20 |
| Word count >= 300 | +30 |
| Word count >= 100 | +15 |

Maximum possible score:

```text
100
```

The scoring logic is intentionally lightweight for evaluation purposes and can be extended later with production-grade SEO rules.

---

# Retry & Failure Handling

Audit processing supports retry-safe asynchronous execution.

Retry configuration:

* Maximum retries: 3
* Retry delay: 30 seconds
* Temporary scraping failures automatically retry
* Permanent failures are marked as failed
* Error messages are stored in database

Handled failure scenarios:

* Request timeout
* HTTP failures
* Invalid URLs
* Connection failures
* Too many redirects
* HTML parsing failures
* Invalid CSV encoding
* Unexpected worker exceptions

This architecture improves resilience against unstable or temporarily unavailable websites.

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
* Filtering
* Duplicate Protection
* Background Processing
* Retry Handling
* Failure Handling

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

Detailed structure:

```text
seo-audit-system/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   ├── projects/
│   └── audits/
└── common/
```

---

# Assumptions

* Simple SEO scoring is sufficient for this assignment.
* No distributed crawling is required.
* Single worker environment is sufficient.
* URLs are processed independently.
* API documentation through Swagger is acceptable as API collection.
* Docker Compose is used for local orchestration.
* Redis is used as Celery broker.
* PostgreSQL is used as primary database.

---

# Tradeoffs

* Mock scoring instead of production SEO engine.
* Simple scraper instead of full crawler.
* Celery task per URL for clarity and traceability.
* Synchronous requests-based scraping instead of fully async aiohttp scraping.
* Focused on backend architecture over crawler complexity.
* No WebSocket progress updates in the core implementation.
* No AI-generated recommendations in the core implementation.

---

# Future Improvements

* Redis caching for dashboard APIs
* Celery Beat periodic re-audits
* Async scraping with aiohttp
* API rate limiting
* AI SEO recommendations
* WebSocket progress updates
* More advanced SEO checks
* Sitemap crawling
* Robots.txt handling
* Export audit reports
* Retry dashboard for failed audits

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
* Duplicate Protection Added
* Retry Handling Added
* Failure Handling Added
* Filtering Added
* Pagination Added
* Dashboard API Added
* Audit Results API Added
