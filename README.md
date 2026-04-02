# Elite SDET Automation Platform



A production-style backend system built with FastAPI and SQL Server, fully Dockerized, transaction-safe, concurrency-tested, and CI-enabled.

This project demonstrates real-world backend engineering practices combined with enterprise-grade automation validation.

---

## Project Overview

Elite SDET Automation Platform is a transactional order management API designed to validate:

OrderFlowX: End-to-End E-commerce Testing Platform

- Concurrency handling
- Idempotency guarantees
- Transaction integrity
- Inventory consistency
- Pagination logic
- State transitions
- CI/CD automation
- Dockerized database isolation
- End-to-end + performance testing

The system simulates production-like behavior under controlled automated validation.

---

## Architecture

Client / UI / Automated Tests  
        ↓  
FastAPI Application Layer  
        ↓  
Service Layer (Business Logic)  
        ↓  
SQL Server (Dockerized)

### Core Architectural Principles

- One transaction per business operation  
- Atomic inventory updates  
- Idempotent order creation  
- Explicit state transition validation  
- Docker-based DB isolation  
- Deterministic test execution  

---

## Technology Stack

Backend: FastAPI  
Database: Microsoft SQL Server 2022 (Docker)  
Driver: pyodbc + ODBC Driver 18  
Testing: pytest (unit, integration, system, e2e, performance)  
UI Testing: Playwright  
CI/CD: GitHub Actions  
Containerization: Docker + Docker Compose 

---

## Core Functional Capabilities

### Order Lifecycle Management
- Create order (Idempotency-Key protected)
- Confirm, ship, complete
- Cancel (with inventory restore)
- Refund flow
- Return lifecycle handling

### Inventory Control
- Atomic stock deduction
- Stock restoration on cancel
- Concurrency-safe SQL updates

### Data Integrity
- SQL row-level locking (UPDLOCK, ROWLOCK)
- Explicit transaction commit/rollback
- Parameterized queries (SQL injection safe)

### Pagination
- OFFSET / FETCH SQL pagination
- Total count metadata

---

## Concurrency & Idempotency Strategy

Order creation is protected using:

- Atomic inventory update with stock >= quantity
- Idempotency-Key header
- Unique constraint on idempotency_key
- Explicit transaction boundaries

This prevents:

- Double order creation
- Overselling stock
- Race condition inconsistencies

---

## Test Pyramid Coverage

Unit Tests  
Integration Tests  
System Tests  
End-to-End Tests 
Performance Tests  

### Current Stable State

- 56 tests passed  
- 2 expected failures (documented edge cases)  
- Full Docker execution  
- CI validation on staging branch  

---

## One-Click Local Execution

### 1. Install Docker Desktop

Ensure Docker is installed and running.

### 2. Clone Repository

git clone https://github.com/spacework639-bit/elite-sdet-automation.git  
cd elite-sdet-automation  

### 3. Run Entire Stack

docker compose down -v  
docker compose up --build --abort-on-container-exit  
or
docker compose up --abort-on-container-exit --no-attach sqlserver --no-attach api

Expected result:

109 passed, 2 xfailed  

No local SQL nothing installation required.

---
## for local including coverage and report 
python -m pytest -v -s
python -m pytest --cov=backend --cov-report=html 
python -m  pytest --cov=backend --cov-report=term-missing
## to run in isolated environment
python -m venv (give any name ex:venv))
venv\scripts\activate


## Docker Architecture

| Service     | Port Mapping     | Purpose |
|-------------|------------------|---------|
| SQL Server  | 14333 → 1433     | Isolated database |
| API         | 8000             | FastAPI application |
| Tests       | Internal network | Automated validation |

Docker SQL runs on port 14333 to avoid collision with Desktop SQL (1433).

---

## Health Endpoints

- /health → Liveness probe  
- /ready → Database readiness check  

---

## Security & Hardening

- Parameterized SQL queries  
- Centralized exception handling  
- Generic 500 error responses  
- Docker-isolated database  
- Environment-based configuration  
- Optional JWT-based auth layer  
- Structured request logging  
- Correlation ID per request  

---

## CI/CD Pipeline

GitHub Actions automatically runs:

- Unit Tests  
- Integration + E2E Tests  
- Performance Tests  

All executed through Docker Compose.

Artifacts generated:
- HTML test reports  
- Coverage reports  

---

## Database Isolation Strategy

Desktop SQL → localhost:1433
Docker SQL → localhost:14333  

Prevents:

- Split-brain database issues  
- Accidental local data contamination  

Verification:

docker exec -it elite_sqlserver \
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P <password> -C \
-Q "SELECT @@SERVERNAME"

---

## Production Readiness Notes

This system includes:

- Transactional integrity  
- Concurrency safety  
- Idempotency protection  
- Structured logging  
- Docker orchestration  
- CI validation  

Recommended enterprise upgrades:

- Secrets manager integration  
- Role-based access control  
- Alembic migrations  
- Connection pooling  
- Observability stack (Prometheus / OpenTelemetry)  

---

## Why This Project Matters

This is not a basic CRUD demo.

It demonstrates:

- Real transactional backend logic  
- Correct concurrency handling  
- Idempotent API design  
- Deterministic automation testing  
- Full Docker orchestration  
- CI-enforced stability  

It reflects production-style engineering combined with automation validation discipline.

---

## Final Verified State

- Docker SQL isolated  
- ODBC Driver 18 configured  
- SSL handled correctly  
- Transaction-safe operations  
- 56 tests passing  
- 2 documented expected failures  
- CI pipeline validated  
- One-command execution ready  

---

Expected Local SLA Failures

Two performance tests (test_order_creation_sla and test_get_product_sla) are expected to fail in local Windows environment.
This is due to DB connection overhead between Windows and Docker (WSL2 bridge + TLS handshake).
Each request pays ~2 seconds for connection setup, exceeding SLA thresholds.

---
## Author

Elite SDET Automation Platform  
Designed for production-style automation validation and backend robustness testing.