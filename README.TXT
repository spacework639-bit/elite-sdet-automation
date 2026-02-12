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
## Conclusion

This framework demonstrates:
- Backend-aware QA engineering
- Strong understanding of transactions and concurrency
- Business-impact-driven testing
- Senior-level SDET thinking

It is designed to prevent real production failures, not just pass automated tests.
