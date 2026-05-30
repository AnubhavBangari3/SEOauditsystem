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

User Request

↓

DRF API Layer

↓

Database Save (Pending Status)

↓

Celery Task Queue

↓

Redis Broker

↓

Background Processing

↓

SEO Scraper

↓

Database Update

↓

Results APIs / Dashboard APIs

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

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

Create:

```bash
.env
```

Run migrations:

```bash
python manage.py migrate
```

Create superuser:

```bash
python manage.py createsuperuser
```

Start server:

```bash
python manage.py runserver
```

---

# Redis Setup

Run Redis:

```bash
docker run --name seo-redis -p 6379:6379 -d redis:7-alpine
```

Verify:

```bash
docker ps
```

---

# Celery Setup

Run worker:

```bash
celery -A config worker -l info --pool=solo
```

---

# Docker Setup

Build:

```bash
docker-compose up --build
```

Stop:

```bash
docker-compose down
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

```
```
