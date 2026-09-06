# ⚡ Performance, Simulation & Load Testing

Performance testing measures the throughput, latency, algorithm efficiency, and server resource utilization of E-Botar under heavy concurrent voter traffic during university peak voting hours.

This directory is part of **Tier 2 (System, Performance, Security & UAT Testing)**, keeping heavy load tests, simulations, and benchmark scripts separate from the core application source code.

---

## 🎯 Key Benchmark Objectives

1. **Concurrent Ballot Submission**:
   - Simulate **500 – 1,000 concurrent student voters** submitting ballots simultaneously.
   - **Target Latency**: 95th percentile (p95) < 500ms for ballot submissions.
   - **Target Throughput**: 100+ transactions per second (TPS).
2. **Blockchain Hash Verification Throughput**:
   - Measure cryptographic verification speed when computing chained SHA-256 blocks during mass ballot verification.
3. **Database & Connection Pool Stability**:
   - Ensure zero database deadlocks or connection starvation under SQLite (local development) and PostgreSQL / MySQL (production).

---

## 📁 Directory Structure & Tool Suite

```text
Testing/Performance/
├── README.md                     <-- Performance criteria, benchmarks & execution guide
├── simulate_concurrent_load.py   <-- Analytical concurrent voter simulation model
├── simulate_output.txt           <-- Baseline simulation report (2,000 population, 120s burst)
├── performance_tests.py          <-- Full API latency, DB query count & algorithm benchmark
├── quick_performance_test.py     <-- Fast smoke test for API latency & core algorithms
├── test_algorithms.py            <-- Algorithmic correctness & execution time benchmarks
└── locustfile.py                 <-- Empirical real-time load testing scenarios (Locust)
```

---

## 🚀 Execution Guide

### 1. Analytical Concurrent Load Simulation (`simulate_concurrent_load.py`)
Models what happens when $N$ users act simultaneously during peak campus voting events based on actual payload sizes, network flows, and DRF throttle rules. Does not require a running server.

```bash
# Default run (2,000 students, 120s burst window, vote_rush scenario)
python Testing/Performance/simulate_concurrent_load.py

# Custom scenario (vote_rush, login_rush, or results_view)
python Testing/Performance/simulate_concurrent_load.py --scenario vote_rush

# Custom student population & concurrent intervals
python Testing/Performance/simulate_concurrent_load.py --total-students 2000 --concurrent 25,50,100,200,500,1000,2000

# Filter by specific server deployment profile (dev_runserver, prod_small, prod_scaled)
python Testing/Performance/simulate_concurrent_load.py --server prod_small
```
> Baseline results are saved in [`simulate_output.txt`](simulate_output.txt).

---

### 2. Live Concurrent Voter Load Testing (`locustfile.py`)
Empirical stress testing simulating real HTTP clients with thinking intervals and credential authentication.

```bash
# 1. Start Django backend
cd backend && python manage.py runserver

# 2. Run Locust from project root
pip install locust
locust -f Testing/Performance/locustfile.py --host=http://localhost:8000
```
Open `http://localhost:8089` to configure user count, spawn rate, and view real-time charts.

---

### 3. Comprehensive Performance & DB Query Benchmark (`performance_tests.py`)
Measures response time latency (p50, p95), requests/sec throughput, database query counts, and algorithm speed, outputting a structured `performance_report.json`.

```bash
python Testing/Performance/performance_tests.py
```

---

### 4. Fast Endpoint & Algorithm Smoke Test (`quick_performance_test.py`)
Quick verification of endpoint response times and core algorithms (sorting, aggregation, searching) with minimal setup.

```bash
python Testing/Performance/quick_performance_test.py
```

---

### 5. Algorithm Correctness & Speed Benchmark (`test_algorithms.py`)
Verifies execution time and correctness for all internal algorithmic implementations:
- Quicksort & Mergesort (sorting candidates and election rosters)
- Binary Search (fast lookups)
- SHA-256 Chaining & RSA (blockchain and receipt verification)
- Multi-level Aggregations (live vote counting)
- Memoization & Cache Keys

```bash
python Testing/Performance/test_algorithms.py
```
