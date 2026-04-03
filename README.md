# OrderFlowX: Concurrency-Safe Order Processing System

A transactional order processing system designed to ensure concurrency safety, idempotency, and data integrity under real-world conditions.

Built using FastAPI, SQL Server, and Docker, this system simulates concurrent order workflows and ensures correctness through deterministic automated testing.

---     
## Failure-Proof Scenarios

### Concurrent Order Race Condition
Two users attempt to purchase the last item simultaneously:

Thread-1 → SUCCESS (order created)  
Thread-2 → FAILED (out of stock)
Response → 409 Conflict (Out of Stock)

✔ Prevents overselling using atomic SQL update + row-level locking.

---

### Idempotent Order Creation

Request-1 (Idempotency-Key: abc123) → Order Created  
Request-2 (same key) → Returned existing order  

✔ Prevents duplicate order creation under retries.

---

### Transaction Rollback (Cancel Flow)

Before cancel → stock = 0  
After cancel → stock = 1  

✔ Ensures inventory consistency via transactional rollback.
## Key Capabilities

- Concurrency-safe order processing
- Idempotent API design using Idempotency-Key
- Transaction-safe inventory updates
- SQL-level locking (UPDLOCK, ROWLOCK)
- State transition validation
- End-to-end + performance testing
- Fully Dockerized execution
- CI/CD validation via GitHub Actions

## Design Decisions

- **Pessimistic locking (UPDLOCK, ROWLOCK):** Prevents race conditions and overselling by acquiring row-level locks during transactions, ensuring safe concurrent updates without escalating to table-level locks.

- **Idempotency-Key strategy:** Ensures repeated requests do not create duplicate orders, making APIs safe under retries.

- **SQL Server choice:** Provides strong transactional guarantees and fine-grained locking control for concurrency-heavy workflows.

## Project Overview

OrderFlowX is a transactional order processing system designed to ensure correctness under concurrent workloads.

It focuses on:

- Safe concurrent order processing without overselling  
- Idempotent request handling to prevent duplicate orders  
- Atomic inventory updates with transaction guarantees  
- State-driven order lifecycle management  
- Deterministic end-to-end testing using Dockerized infrastructure 
---

## Project Structure

```
backend/
├── domain/
│   └── transitions.py              # Defines order state machine and valid state transitions
├── repositories/
│   ├── order_repository.py         # Handles order persistence, queries, and transactional DB operations
│   └── user_repository.py          # Manages user data access and authentication-related DB logic
├── schemas/
│   ├── auth_schema.py              # Pydantic models for auth requests/responses (validation layer)
│   └── order_schema.py             # Data models for order creation, updates, and API contracts
├── services/
│   ├── auth_service.py             # Business logic for authentication and user workflows
│   └── order_service.py            # Core order processing logic (idempotency, concurrency handling)
├── db.py                           # Database connection management and session handling
├── logging_config.py               # Centralized logging setup with structured logs and correlation IDs
└── main.py                         # FastAPI application entry point and route registration

config/
└── config.py                       # Environment configuration (DB settings, secrets, runtime configs)

core/
├── api_client.py                   # Reusable HTTP client for API testing and request abstraction
└── failure_types.py                # Custom error types and failure classification for testing

reporting/
└── excel_report.py                 # Generates structured test reports (Excel format)

reports/
└── screenshots/                   # Stores Playwright/UI test artifacts and failure evidence

tests/
├── api/
│   ├── test_create_order.py        # Validates order creation API (happy path + edge cases)
│   ├── test_cancel_order_api.py    # Tests cancellation flow and inventory restoration
│   ├── test_get_products.py        # Verifies product listing and pagination logic
│   ├── test_main_endpoints.py      # Covers core API endpoints for availability and correctness
│   ├── test_signup.py              # Validates user signup and authentication flows
│   └── test_edge_cases.py          # Covers negative scenarios and input validation failures
├── db/
│   ├── db_utils.py                 # Utility functions for DB setup, teardown, and helpers
│   ├── test_db_insert_rollback.py  # Ensures transactional rollback behavior works correctly
│   ├── test_db_metadata.py         # Validates schema integrity and metadata consistency
│   └── test_db_sanity.py           # Basic DB connectivity and sanity checks
├── e2e/
│   ├── test_order_lifecycle.py     # Full order lifecycle (create → process → complete)
│   ├── test_order_concurrency.py   # Validates concurrent order handling (race conditions)
│   ├── test_order_idempotency.py   # Ensures duplicate requests don’t create duplicate orders
│   ├── test_create_order_api_db.py # Verifies API + DB consistency for order creation
│   └── test_update_product.py      # End-to-end product update validation
├── performance/
│   └── test_sla.py                 # Measures response times and SLA compliance under load
├── services/
│   ├── test_order_service_unit.py  # Unit tests for order service logic
│   └── test_inventory_and_order_service.py # Validates inventory updates with order workflows
├── system/
│   ├── test_orders_system.py       # Cross-component validation (API + DB + services)
│   └── test_db_consistency.py      # Ensures data consistency across operations
├── unit/
│   └── test_transitions.py         # Unit tests for state transition logic
└── helpers/
    └── order_helpers.py            # Shared test utilities and reusable helper functions

# Root Configuration
docker-compose.yml                 # Defines multi-container setup (API + DB + test runner)
Dockerfile                         # Builds application container image
init.sql / schema.sql              # Database schema and initialization scripts
requirements.txt                   # Python dependencies
pytest.ini                         # PyTest configuration and test settings
conftest.py                        # Shared fixtures and test setup configuration
db-init.sh                         # Initializes database inside Docker container
```
## Architecture

Client / Automated Tests  
↓  
FastAPI (API Layer)  
↓  
Service Layer (Business Logic)  
↓  
Repository Layer (Data Access)  
↓  
SQL Server (Dockerized)  

### Core Principles

- One transaction per business operation  
- Atomic inventory updates  
- Idempotent order creation  
- Explicit state transition validation  
- Isolated database using Docker  
- Deterministic test execution  

---

## Technology Stack

- **Backend:** FastAPI  
- **Database:** Microsoft SQL Server 2022 (Docker)  
- **Driver:** pyodbc + ODBC Driver 18  
- **Testing:** PyTest (unit, integration, system, e2e, performance)  
- **UI Testing:** Playwright  
- **CI/CD:** GitHub Actions  
- **Containerization:** Docker + Docker Compose  
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

## Test Coverage

- Unit Tests  
- Integration Tests  
- System Tests  
- End-to-End Tests  
- Performance Tests  

✔ Validates concurrency, idempotency, and transactional integrity under load  
✔ 109 automated tests passing across layers  
✔ Deterministic execution using isolated Docker environment  
✔ CI pipeline enforces test stability on every change  
---
## Run Locally

### Prerequisites

- Docker Desktop installed and running  
- Minimum 8GB RAM recommended  
- WSL2 enabled (for Windows users)  
- Ports 8000 and 14333 must be free  

---

### Docker Execution (Recommended)

#### Clone Repository
```bash
git clone https://github.com/saisubramanyam-dev/elite-sdet-automation.git
cd elite-sdet-automation
```

#### Run Entire Stack
```bash
docker compose down -v  
docker compose up --build --abort-on-container-exit  
```

Alternative:
```bash
docker compose up --abort-on-container-exit --no-attach sqlserver --no-attach api
```

✔ Runs full stack (API + DB + tests)  
✔ No local SQL installation required  
✔ Fully isolated execution  

---

## Local Execution (Optional – Coverage & Reports)

### To run in isolated environment

#### Terminal 1
```bash
python -m venv (give any name ex:venv)
python -m venv venv
venv\scripts\activate
python -m uvicorn backend.main:app
```

#### Terminal 2
```bash
venv\scripts\activate
python -m pytest -v -s
python -m pytest --cov=backend --cov-report=html 
python -m pytest --cov=backend --cov-report=term-missing
```

## Architecture & Infrastructure

### Docker Services

| Service     | Port Mapping     | Purpose                |
|-------------|------------------|------------------------|
| SQL Server  | 14333 → 1433     | Isolated database      |
| API         | 8000             | FastAPI application    |
| Tests       | Internal network | Automated validation   |

Docker SQL runs on port **14333** to avoid conflict with local SQL Server (**1433**).

---

## Health Endpoints

- `/health` → Liveness probe  
- `/ready` → Database readiness check  

---

## Security & Hardening

- Parameterized SQL queries (SQL injection safe)  
- Centralized exception handling  
- Controlled 500 error responses  
- Docker-isolated database environment  
- Environment-based configuration  
- Optional JWT-based authentication  
- Structured request logging  
- Correlation ID per request  

---

## CI/CD Pipeline

GitHub Actions automatically executes:

- Unit Tests  
- Integration + End-to-End Tests  
- Performance Tests  

✔ All tests run via Docker Compose  
✔ Ensures consistent, reproducible execution  

### Artifacts Generated

- HTML test reports  
- Coverage reports  

---

## Database Isolation Strategy

- Local SQL Server → `localhost:1433`  
- Docker SQL Server → `localhost:14333`  

Prevents:

- Split-brain database conflicts  
- Accidental local data contamination  

### Verification

```bash
docker exec -it elite_sqlserver \
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P <password> -C \
-Q "SELECT @@SERVERNAME"
```

## Production Readiness

### Current Capabilities

- Transactional integrity with explicit commit/rollback  
- Concurrency-safe operations under load  
- Idempotent API design to prevent duplicate processing  
- Structured logging with request traceability  
- Fully Dockerized orchestration  
- CI pipeline enforcing automated validation  

### Recommended Enhancements

- Secrets management integration  
- Role-based access control (RBAC)  
- Database migrations (Alembic)  
- Connection pooling optimization  
- Observability stack (Prometheus / OpenTelemetry)  

---

## System Status

- Dockerized SQL Server with isolated environment  
- Secure database connectivity (ODBC Driver 18, SSL enabled)  
- Transaction-safe operations with concurrency protection  
- 109 automated tests passing across all layers  
- CI pipeline validated for consistent execution  
- One-command Docker execution supported  

---

## Performance Note

Certain performance tests may show higher latency in local Windows environments.

Reason:
- Overhead from Docker ↔ WSL2 networking  
- TLS handshake and connection setup cost  

Impact:
- Increased response time (~2s per request)  
- Does not reflect actual service logic performance  

---

## Author

Sai Subramanyam