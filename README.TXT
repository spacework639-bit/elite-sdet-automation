# Production-Grade E-Commerce QA Automation Framework

## Overview

This project is a production-grade QA automation framework focused on validating
business-critical e-commerce workflows using a real backend and a real database.

The goal is not tool usage.
The goal is to protect revenue, data integrity, and system reliability by validating:

- Order correctness
- Inventory integrity
- Idempotency (retry safety)
- Concurrency (race-condition safety)
- Data invariants  
- Failure impact classification
- End-to-end system integration

This framework is designed to catch failures that typically escape QA and appear only in production:
- Overselling
- Duplicate orders
- Double charging
- Inventory corruption under concurrency
- Partial failures during retries
- Silent data inconsistencies

---------------------------------------------------------------------

## Tech Stack

- Language: Python 3.x
- Test Framework: Pytest (fixtures, markers, hooks)
- Backend: FastAPI (real APIs, no mocks)
- Database: SQL Server (real transactions, identity columns, constraints)
- UI Automation: Playwright (Swagger UI)
- HTTP Client: requests
- Reporting: Custom Excel reporter (openpyxl)
- Test Control: pytest-timeout, pytest markers

---------------------------------------------------------------------

## High-Level Architecture

┌────────────────────────┐
│       Test Layer       │
│       (Pytest)         │
│                        │
│ • API tests            │
│ • DB assertions        │
│ • UI tests             │
│ • Idempotency tests    │
│ • Concurrency tests    │
│ • Stress tests         │
│ • Invariant checks     │
└──────────┬─────────────┘
           │ HTTP
           ▼
┌────────────────────────┐
│     FastAPI Backend    │
│     (/orders API)      │
│                        │
│ • Input validation     │
│ • Idempotency handling │
│ • Transaction control  │
│ • Business rules       │
└──────────┬─────────────┘
           │ Atomic SQL
           ▼
┌────────────────────────┐
│        SQL Server      │
│                        │
│ Tables:                │
│ • products             │
│ • inventory            │
│ • orders               │
│                        │
│ Guarantees:            │
│ • Atomicity            │
│ • Consistency          │
│ • Isolation            │
│ • No negative stock    │
└────────────────────────┘

Key Design Principle:
All business safety guarantees are enforced at the database level, not by application-level assumptions.


--------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------

====================================================================================================
                               ELITE SDET AUTOMATION FRAMEWORK
====================================================================================================


                                          ┌─────────────────────────────┐
                                          │         DEVELOPER            │
                                          │  (Manual Testing - Swagger)  │
                                          └──────────────┬──────────────┘
                                                         │
                                                         ▼
                                          ┌─────────────────────────────┐
                                          │     Uvicorn FastAPI Server   │
                                          │   backend.main:app           │
                                          │   http://127.0.0.1:8000      │
                                          └──────────────┬──────────────┘
                                                         │
                                                         ▼
                                          ┌─────────────────────────────┐
                                          │      BUSINESS LOGIC LAYER    │
                                          │  - Order Creation            │
                                          │  - Inventory Reduction       │
                                          │  - Idempotency Validation    │
                                          │  - Input Validation          │
                                          └──────────────┬──────────────┘
                                                         │
                                                         ▼
                                          ┌─────────────────────────────┐
                                          │        SQL SERVER DB         │
                                          │  - products                  │
                                          │  - inventory                 │
                                          │  - orders                    │
                                          └─────────────────────────────┘



====================================================================================================
                                   AUTOMATED TESTING ARCHITECTURE
====================================================================================================


                                   ┌───────────────────────────────┐
                                   │            pytest              │
                                   │       (Test Runner Engine)     │
                                   └───────────────┬───────────────┘
                                                   │
         ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
         │                                         │                                         │
         ▼                                         ▼                                         ▼

┌──────────────────────┐              ┌──────────────────────┐              ┌──────────────────────┐
│     API TESTS        │              │     DB VALIDATION    │              │      UI TESTS        │
│ (Business Rules)     │              │   (Data Integrity)   │              │   (Playwright)       │
└──────────┬───────────┘              └──────────┬───────────┘              └──────────┬───────────┘
           │                                      │                                      │
           ▼                                      ▼                                      ▼

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FASTAPI APPLICATION                                        │
│                                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ ROUTES                                                                                  │  │
│  │  POST /orders                                                                           │  │
│  │  GET  /orders/{id}                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ BUSINESS LOGIC                                                                          │  │
│  │  - Validate quantity                                                                    │  │
│  │  - Check inventory stock                                                                │  │
│  │  - Handle idempotency keys                                                              │  │
│  │  - Prevent race conditions                                                               │  │
│  │  - Calculate total price                                                                 │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ DATA ACCESS LAYER                                                                       │  │
│  │  - Insert into orders                                                                   │  │
│  │  - Update inventory                                                                     │  │
│  │  - Transaction management                                                               │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
                                   ┌───────────────────────────────┐
                                   │        SQL SERVER (CI)        │
                                   │  Docker Service Container     │
                                   │  Schema initialized in CI     │
                                   └───────────────────────────────┘



====================================================================================================
                                   CI PIPELINE FLOW (GitHub Actions)
====================================================================================================


┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                GITHUB ACTIONS WORKFLOW                                       │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  1. Checkout Code                                                                            │
│  2. Setup Python 3.11                                                                        │
│  3. Install ODBC + SQL Tools                                                                 │
│  4. Start SQL Server Docker Container                                                        │
│  5. Wait Until DB Is Ready                                                                   │
│  6. Create TravelXDB + Apply schema.sql                                                      │
│  7. Install Dependencies (pytest, playwright, pytest-html, pytest-cov)                     │
│  8. Run Tests                                                                                │
│  9. Generate Reports                                                                         │
│ 10. Measure Coverage                                                                         │
│ 11. Upload Artifacts (HTML + XML Reports)                                                    │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘



====================================================================================================
                                       QUALITY ENGINEERING LAYERS
====================================================================================================

✔ API Layer Testing (Business Logic Validation)
✔ Database State Verification (Post-condition checks)
✔ Concurrency Testing (Race Condition Validation)
✔ Idempotency Testing (Duplicate Request Safety)
✔ UI Automation (Playwright Browser Layer)
✔ CI Pipeline Orchestration
✔ Dockerized SQL Server in CI
✔ Coverage Measurement
✔ Artifact Reporting


====================================================================================================
                                   SYSTEM THINKING OVERVIEW
====================================================================================================

Manual Mode:
    Developer → Uvicorn → FastAPI → SQL Server

Automated Mode:
    pytest → FastAPI (in-process or via HTTP) → SQL Server

CI Mode:
    GitHub Actions → Docker SQL → Schema Init → pytest → Reports → Coverage


====================================================================================================


---------------------------------------------------------------------

## Core Business Flow

POST /orders

Responsibilities:
- Read product price from database
- Validate inventory availability
- Enforce idempotency using Idempotency-Key
- Atomically reduce inventory
- Insert order row
- Commit or rollback transaction safely
- Return deterministic response for retries

---------------------------------------------------------------------

## Why This Project Is Different

Typical QA automation projects:
- Mock backend services
- Skip database verification
- Ignore race conditions
- Test only happy paths
- Validate only HTTP responses

This project:
- Uses real backend services
- Uses real SQL Server transactions
- Validates database side effects
- Tests retry safety and race safety separately
- Focuses on failure prevention, not just correctness
- Treats database as the source of truth

This mirrors how real e-commerce and payment systems are tested in production.

---------------------------------------------------------------------

## Key Test Scenarios

1. Core Order → Inventory Flow (API + DB)
- Validates order creation
- Validates correct inventory deduction
- Validates order persistence
- Validates DB consistency
Why it matters: direct revenue impact

2. Idempotency (Retry Safety)
Scenario:
- Same request retried multiple times
- Same Idempotency-Key
Expected:
- Only one order created
- Inventory reduced exactly once
- Same order ID returned
Why it matters:
- Prevents duplicate charges
- Handles network retries safely
Important:
- Idempotency protects retries, NOT concurrency

3. Concurrency Race-Condition Test (Stock = 1)
Scenario:
- Inventory stock = 1
- Two parallel requests
- Different Idempotency-Keys
Expected:
- One success (200)
- One failure (409)
- Inventory ends at 0
- Exactly one order in DB
Why it matters:
- Proves race-condition safety
- Prevents overselling

4. Concurrency Stress Test (Demand > Supply)
Scenario:
- Inventory stock = 5
- 10 parallel requests
Expected:
- 5 succeed
- 5 fail
- No overselling
- Inventory never negative
Why it matters:
- Validates correctness under contention
- Exposes weak transaction handling

5. UI → API → DB End-to-End Flow
Scenario:
- Swagger UI automated via Playwright
- Order placed through UI
- Database verified after UI action
Why it matters:
- Confirms full system integration
- Validates UI-to-backend wiring

---------------------------------------------------------------------

## Data Invariants (Always Enforced)

The following invariant must always hold true:

orders_created + remaining_stock = initial_stock

If this invariant breaks:
- System is in a corrupt state
- Release must be blocked

Invariant validation is part of automated tests.

---------------------------------------------------------------------

## Failure Classification & Release Blocking

Each test can declare:
- Failure type (BUSINESS / TECHNICAL)
- Severity (LOW / MEDIUM / HIGH / CRITICAL)
- Release-blocker flag

Examples of release-blocking failures:
- Overselling
- Duplicate orders
- Inventory mismatch
- Idempotency violations

Critical failures immediately block release.

---------------------------------------------------------------------

## Test Execution Commands

Start Backend:
python -m uvicorn backend.main:app --reload

Run Core E2E Tests:
python -m pytest tests/e2e -m e2e -v

Run Idempotency Tests:
python -m pytest tests/e2e/test_order_idempotency.py -m idempotency -v

Run Concurrency Test (Stock = 1):
python -m pytest tests/e2e/test_order_concurrency.py -v

Run Concurrency Stress Test:
python -m pytest tests/e2e/test_order_concurrency_stress.py -v

Run UI End-to-End Test:
python -m pytest tests/ui/test_place_order_ui.py --headed --slowmo 1000 -v


---------------------------------------------------------------------

## Reporting & Evidence

On failure:
- Screenshots captured automatically (UI tests)
- Excel report generated containing:
  - Test name
  - Execution status
  - Failure category
  - Severity
  - Release-blocker indicator

This makes the framework suitable for CI/CD, audits, and stakeholder reporting.

---------------------------------------------------------------------

## Engineering Principles Followed

- Database is the single source of truth
- Atomic SQL over application-level checks
- Idempotency and concurrency treated as separate risk classes
- No shared test data across tests
- Deterministic and repeatable test runs
- Explicit cleanup after every test
- Fail fast on business risk

---------------------------------------------------------------------

## Interview-Ready Explanations

Why test idempotency and concurrency separately?
Idempotency handles retries of the same request, while concurrency handles multiple independent requests racing for limited inventory. They solve different classes of failures and must be tested independently.

Why enforce inventory rules at DB level?
Application-level checks fail under parallel execution. Atomic SQL guarantees correctness even under concurrency.

How is overselling prevented?
Inventory is deducted using conditional atomic updates that ensure stock never goes below zero.

Why validate database state in QA?
APIs can return success even when data is corrupted. Database state is the only reliable source of truth.

What makes this framework production-grade?
Real backend, real database, transaction-level validation, concurrency and stress testing, invariant checks, failure classification, and release-blocking logic.

---------------------------------------------------------------------

HOW TO RUN LOCALLY
====================================================================

1. Create virtual environment:
   python -m venv venv(you can create any name after venv )

2. Activate:
   .\venv\Scripts\Activate.ps1

3. Install dependencies:
   pip install -r requirements.txt

4. Install Playwright browsers:
   playwright install

5. Run full suite:
   python -m pytest 
  python -m pytest -s (allow to print statement) 
----------------------------------------------------------------------
#python -c "import sys; print(sys.executable)"(To check weather your in active envinorment)

Backend auto-starts.
Backend auto-stops.
Excel report generated.
Screenshots saved for failures.
----------------------------------------------------------------------------------


========================================
TEST REPORTING & COVERAGE EXPLANATION
========================================

This project generates professional CI test reports and code coverage
metrics using pytest, pytest-html, and pytest-cov.

----------------------------------------
1) --junitxml=reports/report.xml
----------------------------------------

What it does:
Generates a machine-readable XML test report.

Why it matters:
CI systems understand XML format. This allows:
- Integration with dashboards
- Test analytics
- Historical tracking
- Future SonarQube integration

Example:
If 10 tests run and 2 fail,
report.xml will contain structured data showing:
- Total tests: 10
- Passed: 8
- Failed: 2
- Execution time per test


----------------------------------------
2) --html=reports/report.html
   --self-contained-html
----------------------------------------

What it does:
Generates a human-readable HTML report.

Why it matters:
You can visually inspect:
- Which tests passed/failed
- Execution duration
- Error tracebacks
- Environment details

Example:
If test_order_creation fails,
the HTML report shows:
- Test name
- Failure reason
- Full assertion message
- Stack trace

--self-contained-html ensures:
All CSS and JS are embedded in the file.
The report works standalone when downloaded.


----------------------------------------
3) --cov=backend
----------------------------------------

What it does:
Measures how much of the backend code is executed during tests.

Why it matters:
Prevents fake confidence.
If code is not executed, it is not truly tested.

Example:

backend/orders.py

def calculate_total(price, quantity):
    return price * quantity

If no test calls calculate_total(),
coverage will show this line in RED.

If a test calls it:
coverage shows it in GREEN.


----------------------------------------
4) --cov-report=xml:reports/coverage.xml
----------------------------------------

What it does:
Creates machine-readable coverage data.

Why it matters:
Used for:
- CI quality gates
- Code coverage badges
- External analysis tools


----------------------------------------
5) --cov-report=html:reports/coverage-html
----------------------------------------

What it does:
Creates visual coverage dashboard.

Inside:
reports/coverage-html/index.html

When opened:
- Green lines = tested
- Red lines = untested
- Percentage per file
- Total project coverage %

Example:
orders.py → 92%
database.py → 60%
Total Project → 84%

python -m pytest --cov=backend --cov-report=term-missing -k "not ui"(to print missing lines never executed)

python -m pytest --cov=backend --cov-fail-under=80 -k "not ui"(to test coverage percentage)

python -m pytest --cov=backend
note:we are using not ui bcz we are ignoring ui testing here



----------------------------------------
WHY THIS IS IMPORTANT
----------------------------------------

Without coverage:
You only know tests pass.

With coverage:
You know:
- How much of the system is exercised
- Where risk areas exist
- What needs additional tests


----------------------------------------
CI OUTPUT STRUCTURE
----------------------------------------

reports/
│
├── report.xml
├── report.html
├── coverage.xml
└── coverage-html/
    └── index.html


----------------------------------------
ENGINEERING MATURITY
----------------------------------------

This pipeline:
- Generates machine-readable reports
- Generates human-readable reports
- Measures real code coverage
- Uploads artifacts for inspection
- Enables future quality gates

This demonstrates:
- CI awareness
- Quality engineering discipline
- Enterprise-level reporting practices
----------------------------------------------------------------------------
## Conclusion

This framework demonstrates:
- Backend-aware QA engineering
- Strong understanding of transactions and concurrency
- Business-impact-driven testing
- Senior-level SDET thinking

It is designed to prevent real production failures, not just pass automated tests.
