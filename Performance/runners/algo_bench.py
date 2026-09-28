#!/usr/bin/env python
"""
Cross-Language Algorithm Benchmark Runner - Python Backend.
Executes standardized algorithm workloads and emits conforming JSON result contracts.
"""
import sys
import time
import math
import json
import random
import argparse
import tracemalloc
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def run_heap_sort(dataset_size: int = 50000) -> Dict[str, Any]:
    """Execute in-place Heap Sort with comparison and swap tracking."""
    # Deterministic dataset generation (fixed seed for cross-language reproducibility)
    rng = random.Random(42)
    arr = [rng.randint(0, 1000000) for _ in range(dataset_size)]

    comparisons = 0
    swaps = 0

    def heapify(n: int, i: int):
        nonlocal comparisons, swaps
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2

        if left < n:
            comparisons += 1
            if arr[left] > arr[largest]:
                largest = left

        if right < n:
            comparisons += 1
            if arr[right] > arr[largest]:
                largest = right

        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            swaps += 1
            heapify(n, largest)

    tracemalloc.start()
    start_time = time.perf_counter()

    # Build max-heap
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)

    # Extract elements from heap
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        swaps += 1
        heapify(i, 0)

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Verify correctness
    is_sorted = all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))

    return {
        "dataset_size": dataset_size,
        "duration_ms": round(duration_ms, 3),
        "comparisons": comparisons,
        "swaps": swaps,
        "peak_memory_kb": round(peak_bytes / 1024.0, 2),
        "correctness_verified": is_sorted
    }


def run_hash_table(dataset_size: int = 100000, lookup_keys: int = 5000) -> Dict[str, Any]:
    """Evaluate O(1) Hash Table lookup latency across random keys."""
    # Populate dictionary
    table = {f"item_key_{i}": i * 7 for i in range(dataset_size)}

    # Prepare lookup keys: half existing, half synthetic/missing
    rng = random.Random(1337)
    queries = []
    for _ in range(lookup_keys // 2):
        k = rng.randint(0, dataset_size - 1)
        queries.append(f"item_key_{k}")
    for _ in range(lookup_keys - len(queries)):
        k = rng.randint(dataset_size, dataset_size * 2)
        queries.append(f"item_missing_{k}")

    # Measure lookup duration
    found_count = 0
    start_time = time.perf_counter()
    for query in queries:
        if query in table:
            found_count += 1
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    avg_lookup_us = (duration_ms * 1000.0) / max(lookup_keys, 1)
    correctness_verified = found_count == (lookup_keys // 2)

    return {
        "dataset_size": dataset_size,
        "lookup_keys": lookup_keys,
        "duration_ms": round(duration_ms, 3),
        "avg_lookup_us": round(avg_lookup_us, 4),
        "found_count": found_count,
        "correctness_verified": correctness_verified
    }


def run_fibonacci(target_n: int = 30) -> Dict[str, Any]:
    """Execute dual Fibonacci (naive recursive vs linear memoized) with runaway guard."""
    # Hard safety guard cap
    n = min(max(target_n, 1), 32)

    # 1. Naive recursive
    def fib_naive(val: int) -> int:
        if val <= 1:
            return val
        return fib_naive(val - 1) + fib_naive(val - 2)

    start_naive = time.perf_counter()
    naive_res = fib_naive(n)
    naive_duration_ms = (time.perf_counter() - start_naive) * 1000.0

    # 2. Linear memoized / iterative
    start_memo = time.perf_counter()
    if n <= 1:
        memo_res = n
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        memo_res = b
    memo_duration_ms = (time.perf_counter() - start_memo) * 1000.0

    speedup = naive_duration_ms / max(memo_duration_ms, 0.0001)
    correctness_verified = (naive_res == memo_res)

    return {
        "n": n,
        "naive_duration_ms": round(naive_duration_ms, 3),
        "memoized_duration_ms": round(memo_duration_ms, 4),
        "speedup_factor": round(speedup, 2),
        "expected_result": memo_res,
        "actual_result": naive_res,
        "correctness_verified": correctness_verified
    }


def run_monte_carlo_pi(samples: int = 1000000) -> Dict[str, Any]:
    """Estimate Pi via Monte Carlo random quarter-circle hit ratio."""
    rng = random.Random(999)
    inside_count = 0

    start_time = time.perf_counter()
    for _ in range(samples):
        x = rng.random()
        y = rng.random()
        if x * x + y * y <= 1.0:
            inside_count += 1
    duration_sec = time.perf_counter() - start_time
    duration_ms = duration_sec * 1000.0

    estimated_pi = 4.0 * (inside_count / samples)
    actual_pi = math.pi
    abs_error = abs(estimated_pi - actual_pi)
    samples_per_sec = samples / max(duration_sec, 0.00001)

    # Statistical tolerance: adaptive based on sample volume
    tolerance = 0.05 if samples < 100000 else 0.01
    correctness_verified = abs_error < tolerance

    return {
        "samples": samples,
        "estimated_pi": round(estimated_pi, 6),
        "actual_pi": round(actual_pi, 6),
        "absolute_error": round(abs_error, 6),
        "duration_ms": round(duration_ms, 3),
        "samples_per_sec": round(samples_per_sec, 1),
        "correctness_verified": correctness_verified
    }


def execute_all_benchmarks(
    dataset_size: int = 50000,
    lookup_keys: int = 5000,
    fib_n: int = 30,
    pi_samples: int = 1000000
) -> Dict[str, Any]:
    """Run all 4 cross-language workloads and package into standardized contract."""
    start_total = time.perf_counter()

    heap_res = run_heap_sort(dataset_size)
    hash_res = run_hash_table(dataset_size * 2, lookup_keys)
    fib_res = run_fibonacci(fib_n)
    pi_res = run_monte_carlo_pi(pi_samples)

    total_duration_ms = (time.perf_counter() - start_total) * 1000.0

    v = sys.version_info
    return {
        "runtime": "python",
        "version": f"Python {v.major}.{v.minor}.{v.micro}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_duration_ms": round(total_duration_ms, 3),
        "workloads": {
            "heap_sort": heap_res,
            "hash_table": hash_res,
            "fibonacci": fib_res,
            "monte_carlo_pi": pi_res
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Python Cross-Language Algorithm Benchmark Runner")
    parser.add_argument("--json", action="store_true", help="Output standardized JSON contract to stdout")
    parser.add_argument("--dataset", type=int, default=50000, help="Heap sort dataset size (default: 50,000)")
    parser.add_argument("--lookups", type=int, default=5000, help="Hash table lookup query count (default: 5,000)")
    parser.add_argument("--fib-n", type=int, default=30, help="Target Fibonacci integer (default: 30, max: 32)")
    parser.add_argument("--samples", type=int, default=1000000, help="Monte Carlo Pi sample points (default: 1,000,000)")

    args = parser.parse_args()

    result = execute_all_benchmarks(
        dataset_size=args.dataset,
        lookup_keys=args.lookups,
        fib_n=args.fib_n,
        pi_samples=args.samples
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"⚡ Python Algorithm Benchmarks ({result['version']}):")
        print(f"  • Heap Sort ({result['workloads']['heap_sort']['dataset_size']} items): {result['workloads']['heap_sort']['duration_ms']} ms (Swaps: {result['workloads']['heap_sort']['swaps']})")
        print(f"  • Hash Table ({result['workloads']['hash_table']['lookup_keys']} queries): {result['workloads']['hash_table']['duration_ms']} ms (Avg: {result['workloads']['hash_table']['avg_lookup_us']} µs/op)")
        print(f"  • Fibonacci (N={result['workloads']['fibonacci']['n']}): {result['workloads']['fibonacci']['naive_duration_ms']} ms (Speedup: {result['workloads']['fibonacci']['speedup_factor']}x)")
        print(f"  • Monte Carlo Pi ({result['workloads']['monte_carlo_pi']['samples']} pts): {result['workloads']['monte_carlo_pi']['duration_ms']} ms (Est: {result['workloads']['monte_carlo_pi']['estimated_pi']}, Err: {result['workloads']['monte_carlo_pi']['absolute_error']})")
        print(f"  Total Duration: {result['total_duration_ms']} ms")


if __name__ == "__main__":
    main()
