# ⚡ Performance, Concurrency & Reliability Testing Engine

Framework-agnostic performance benchmarks, computational stress tests, and analytical concurrent-load simulations designed to evaluate web services, REST APIs, and core algorithms.

This directory is an independent testing module operating completely on Python standard library primitives.

---

## 🎯 Key Objectives

1. **Analytical Concurrency Simulation**:
   - Model high-concurrency peak traffic events (50 to 5,000+ concurrent simulated users) across standard industry web profiles (`balanced_api`, `read_heavy`, `write_heavy`, `burst_ping`).
   - Calculate outbound bandwidth/egress, arrival requests per second (req/s), and server utilization curves.
2. **Hardware Sizing & Reliability Thresholds**:
   - Compute capacity envelopes across development, host multi-core hardware, and cloud production environments.
   - Detect bottlenecks and forecast system degradation states (`OPTIMAL`, `HEALTHY`, `SATURATED`, `OVERLOADED`, `CRITICAL`).
3. **Algorithmic Correctness & Memory Benchmarks**:
   - Verify sorting, searching, hashing, and cache lookups against expected output assertions.
   - Profile execution duration (nanoseconds/milliseconds) and peak RAM consumption (`tracemalloc`).

---

## 📁 Directory Structure

```text
Performance/
├── README.md              <-- Performance criteria, benchmarks & execution guide
├── reliability_tester.py  <-- Analytical concurrent load & reliability simulation model
└── algorithm_tester.py    <-- Algorithmic correctness assertions & speed benchmarks
```

---

## 🚀 Execution Guide

### 1. Analytical Concurrency & Reliability Simulation (`reliability_tester.py`)
Simulates traffic patterns and assesses reliability thresholds without requiring a running backend server:

```bash
# Default balanced API run with 50, 100, 500, 1000 concurrent users
python Performance/reliability_tester.py

# Custom traffic scenario (balanced_api, read_heavy, write_heavy, burst_ping, or all)
python Performance/reliability_tester.py --scenario read_heavy --concurrent 500

# Specify custom concurrency counts and burst window (seconds)
python Performance/reliability_tester.py --concurrent 100,500,2000 --burst-seconds 60

# Filter by target server profile (dev_single_worker, host_hardware, cloud_small, cloud_scaled)
python Performance/reliability_tester.py --server host_hardware --concurrent 1000
```

### 2. Algorithmic Correctness & Speed Benchmark (`algorithm_tester.py`)
Runs mathematical benchmarks and correctness assertions across standard computer science workloads:
- Quicksort & Binary Search (lookups & sorting stability)
- SHA-256 Hashing & Digest Throughput
- Memory Pressure & Cache Profiling

```bash
python Performance/algorithm_tester.py
```
