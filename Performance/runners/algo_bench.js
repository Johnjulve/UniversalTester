#!/usr/bin/env node
/**
 * Cross-Language Algorithm Benchmark Runner - Node.js Backend.
 * Executes standardized algorithm workloads and emits conforming JSON result contracts.
 */
const { performance } = require('perf_hooks');

// Simple seedable pseudo-random generator (LCG) for deterministic reproducibility
function createRng(seed = 42) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return function() {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function runHeapSort(datasetSize = 50000) {
  const rng = createRng(42);
  const arr = new Int32Array(datasetSize);
  for (let i = 0; i < datasetSize; i++) {
    arr[i] = Math.floor(rng() * 1000000);
  }

  let comparisons = 0;
  let swaps = 0;

  function heapify(n, i) {
    let largest = i;
    const left = 2 * i + 1;
    const right = 2 * i + 2;

    if (left < n) {
      comparisons++;
      if (arr[left] > arr[largest]) {
        largest = left;
      }
    }

    if (right < n) {
      comparisons++;
      if (arr[right] > arr[largest]) {
        largest = right;
      }
    }

    if (largest !== i) {
      const temp = arr[i];
      arr[i] = arr[largest];
      arr[largest] = temp;
      swaps++;
      heapify(n, largest);
    }
  }

  const startMem = process.memoryUsage().heapUsed;
  const startTime = performance.now();

  const n = arr.length;
  for (let i = Math.floor(n / 2) - 1; i >= 0; i--) {
    heapify(n, i);
  }

  for (let i = n - 1; i > 0; i--) {
    const temp = arr[0];
    arr[0] = arr[i];
    arr[i] = temp;
    swaps++;
    heapify(i, 0);
  }

  const durationMs = performance.now() - startTime;
  const endMem = process.memoryUsage().heapUsed;
  const peakKb = Math.max((endMem - startMem) / 1024.0, (datasetSize * 4) / 1024.0);

  let isSorted = true;
  for (let i = 0; i < n - 1; i++) {
    if (arr[i] > arr[i + 1]) {
      isSorted = false;
      break;
    }
  }

  return {
    dataset_size: datasetSize,
    duration_ms: Number(durationMs.toFixed(3)),
    comparisons,
    swaps,
    peak_memory_kb: Number(peakKb.toFixed(2)),
    correctness_verified: isSorted
  };
}

function runHashTable(datasetSize = 100000, lookupKeys = 5000) {
  const table = new Map();
  for (let i = 0; i < datasetSize; i++) {
    table.set(`item_key_${i}`, i * 7);
  }

  const rng = createRng(1337);
  const queries = [];
  const half = Math.floor(lookupKeys / 2);
  for (let i = 0; i < half; i++) {
    const k = Math.floor(rng() * datasetSize);
    queries.push(`item_key_${k}`);
  }
  for (let i = 0; i < lookupKeys - half; i++) {
    const k = Math.floor(rng() * datasetSize) + datasetSize;
    queries.push(`item_missing_${k}`);
  }

  let foundCount = 0;
  const startTime = performance.now();
  for (let i = 0; i < queries.length; i++) {
    if (table.has(queries[i])) {
      foundCount++;
    }
  }
  const durationMs = performance.now() - startTime;
  const avgLookupUs = (durationMs * 1000.0) / Math.max(lookupKeys, 1);

  return {
    dataset_size: datasetSize,
    lookup_keys: lookupKeys,
    duration_ms: Number(durationMs.toFixed(3)),
    avg_lookup_us: Number(avgLookupUs.toFixed(4)),
    found_count: foundCount,
    correctness_verified: foundCount === half
  };
}

function runFibonacci(targetN = 30) {
  const n = Math.min(Math.max(targetN, 1), 32);

  function fibNaive(val) {
    if (val <= 1) return val;
    return fibNaive(val - 1) + fibNaive(val - 2);
  }

  const startNaive = performance.now();
  const naiveRes = fibNaive(n);
  const naiveDurationMs = performance.now() - startNaive;

  const startMemo = performance.now();
  let memoRes;
  if (n <= 1) {
    memoRes = n;
  } else {
    let a = 0;
    let b = 1;
    for (let i = 2; i <= n; i++) {
      const next = a + b;
      a = b;
      b = next;
    }
    memoRes = b;
  }
  const memoDurationMs = performance.now() - startMemo;

  const speedup = naiveDurationMs / Math.max(memoDurationMs, 0.0001);

  return {
    n,
    naive_duration_ms: Number(naiveDurationMs.toFixed(3)),
    memoized_duration_ms: Number(memoDurationMs.toFixed(4)),
    speedup_factor: Number(speedup.toFixed(2)),
    expected_result: memoRes,
    actual_result: naiveRes,
    correctness_verified: naiveRes === memoRes
  };
}

function runMonteCarloPi(samples = 1000000) {
  const rng = createRng(999);
  let insideCount = 0;

  const startTime = performance.now();
  for (let i = 0; i < samples; i++) {
    const x = rng();
    const y = rng();
    if (x * x + y * y <= 1.0) {
      insideCount++;
    }
  }
  const durationMs = performance.now() - startTime;
  const durationSec = durationMs / 1000.0;

  const estimatedPi = 4.0 * (insideCount / samples);
  const actualPi = Math.PI;
  const absError = Math.abs(estimatedPi - actualPi);
  const samplesPerSec = samples / Math.max(durationSec, 0.00001);

  return {
    samples,
    estimated_pi: Number(estimatedPi.toFixed(6)),
    actual_pi: Number(actualPi.toFixed(6)),
    absolute_error: Number(absError.toFixed(6)),
    duration_ms: Number(durationMs.toFixed(3)),
    samples_per_sec: Number(samplesPerSec.toFixed(1)),
    correctness_verified: absError < (samples < 100000 ? 0.05 : 0.01)
  };
}

function executeAllBenchmarks(datasetSize = 50000, lookupKeys = 5000, fibN = 30, piSamples = 1000000) {
  const startTotal = performance.now();

  const heapRes = runHeapSort(datasetSize);
  const hashRes = runHashTable(datasetSize * 2, lookupKeys);
  const fibRes = runFibonacci(fibN);
  const piRes = runMonteCarloPi(piSamples);

  const totalDurationMs = performance.now() - startTotal;

  return {
    runtime: "node",
    version: `Node.js ${process.version}`,
    timestamp: new Date().toISOString(),
    total_duration_ms: Number(totalDurationMs.toFixed(3)),
    workloads: {
      heap_sort: heapRes,
      hash_table: hashRes,
      fibonacci: fibRes,
      monte_carlo_pi: piRes
    }
  };
}

function main() {
  const args = process.argv.slice(2);
  const isJson = args.includes('--json');

  let datasetSize = 50000;
  let lookupKeys = 5000;
  let fibN = 30;
  let piSamples = 1000000;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--dataset' && args[i + 1]) datasetSize = parseInt(args[i + 1], 10);
    if (args[i] === '--lookups' && args[i + 1]) lookupKeys = parseInt(args[i + 1], 10);
    if (args[i] === '--fib-n' && args[i + 1]) fibN = parseInt(args[i + 1], 10);
    if (args[i] === '--samples' && args[i + 1]) piSamples = parseInt(args[i + 1], 10);
  }

  const result = executeAllBenchmarks(datasetSize, lookupKeys, fibN, piSamples);

  if (isJson) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`Node.js Algorithm Benchmarks (${result.version}):`);
    console.log(`  • Heap Sort (${result.workloads.heap_sort.dataset_size} items): ${result.workloads.heap_sort.duration_ms} ms (Swaps: ${result.workloads.heap_sort.swaps})`);
    console.log(`  • Hash Table (${result.workloads.hash_table.lookup_keys} queries): ${result.workloads.hash_table.duration_ms} ms (Avg: ${result.workloads.hash_table.avg_lookup_us} µs/op)`);
    console.log(`  • Fibonacci (N=${result.workloads.fibonacci.n}): ${result.workloads.fibonacci.naive_duration_ms} ms (Speedup: ${result.workloads.fibonacci.speedup_factor}x)`);
    console.log(`  • Monte Carlo Pi (${result.workloads.monte_carlo_pi.samples} pts): ${result.workloads.monte_carlo_pi.duration_ms} ms (Est: ${result.workloads.monte_carlo_pi.estimated_pi}, Err: ${result.workloads.monte_carlo_pi.absolute_error})`);
    console.log(`  Total Duration: ${result.total_duration_ms} ms`);
  }
}

if (require.main === module) {
  main();
}

module.exports = { executeAllBenchmarks };
