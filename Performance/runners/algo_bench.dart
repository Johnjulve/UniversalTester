// Cross-Language Algorithm Benchmark Runner - Dart Backend.
// Executes standardized algorithm workloads and emits conforming JSON result contracts.

import 'dart:io';
import 'dart:math';
import 'dart:convert';

Map<String, dynamic> runHeapSort([int datasetSize = 50000]) {
  final rng = Random(42);
  final List<int> arr = List<int>.generate(datasetSize, (_) => rng.nextInt(1000000), growable: false);

  int comparisons = 0;
  int swaps = 0;

  void heapify(int n, int i) {
    int largest = i;
    final int left = 2 * i + 1;
    final int right = 2 * i + 2;

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

    if (largest != i) {
      final int temp = arr[i];
      arr[i] = arr[largest];
      arr[largest] = temp;
      swaps++;
      heapify(n, largest);
    }
  }

  final stopwatch = Stopwatch()..start();

  final int n = arr.length;
  for (int i = (n ~/ 2) - 1; i >= 0; i--) {
    heapify(n, i);
  }

  for (int i = n - 1; i > 0; i--) {
    final int temp = arr[0];
    arr[0] = arr[i];
    arr[i] = temp;
    swaps++;
    heapify(i, 0);
  }

  stopwatch.stop();
  final double durationMs = stopwatch.elapsedMicroseconds / 1000.0;
  final double peakKb = (ProcessInfo.currentRss / 1024.0);

  bool isSorted = true;
  for (int i = 0; i < n - 1; i++) {
    if (arr[i] > arr[i + 1]) {
      isSorted = false;
      break;
    }
  }

  return {
    'dataset_size': datasetSize,
    'duration_ms': double.parse(durationMs.toStringAsFixed(3)),
    'comparisons': comparisons,
    'swaps': swaps,
    'peak_memory_kb': double.parse(peakKb.toStringAsFixed(2)),
    'correctness_verified': isSorted,
  };
}

Map<String, dynamic> runHashTable([int datasetSize = 100000, int lookupKeys = 5000]) {
  final Map<String, int> table = {};
  for (int i = 0; i < datasetSize; i++) {
    table['item_key_$i'] = i * 7;
  }

  final rng = Random(1337);
  final List<String> queries = [];
  final int half = lookupKeys ~/ 2;

  for (int i = 0; i < half; i++) {
    final int k = rng.nextInt(datasetSize);
    queries.add('item_key_$k');
  }
  for (int i = 0; i < lookupKeys - half; i++) {
    final int k = rng.nextInt(datasetSize) + datasetSize;
    queries.add('item_missing_$k');
  }

  int foundCount = 0;
  final stopwatch = Stopwatch()..start();
  for (int i = 0; i < queries.length; i++) {
    if (table.containsKey(queries[i])) {
      foundCount++;
    }
  }
  stopwatch.stop();

  final double durationMs = stopwatch.elapsedMicroseconds / 1000.0;
  final double avgLookupUs = (durationMs * 1000.0) / max(lookupKeys, 1);

  return {
    'dataset_size': datasetSize,
    'lookup_keys': lookupKeys,
    'duration_ms': double.parse(durationMs.toStringAsFixed(3)),
    'avg_lookup_us': double.parse(avgLookupUs.toStringAsFixed(4)),
    'found_count': foundCount,
    'correctness_verified': foundCount == half,
  };
}

Map<String, dynamic> runFibonacci([int targetN = 30]) {
  final int n = min(max(targetN, 1), 32);

  int fibNaive(int val) {
    if (val <= 1) return val;
    return fibNaive(val - 1) + fibNaive(val - 2);
  }

  final swNaive = Stopwatch()..start();
  final int naiveRes = fibNaive(n);
  swNaive.stop();
  final double naiveDurationMs = swNaive.elapsedMicroseconds / 1000.0;

  final swMemo = Stopwatch()..start();
  int memoRes;
  if (n <= 1) {
    memoRes = n;
  } else {
    int a = 0;
    int b = 1;
    for (int i = 2; i <= n; i++) {
      final int next = a + b;
      a = b;
      b = next;
    }
    memoRes = b;
  }
  swMemo.stop();
  final double memoDurationMs = swMemo.elapsedMicroseconds / 1000.0;

  final double speedup = naiveDurationMs / max(memoDurationMs, 0.0001);

  return {
    'n': n,
    'naive_duration_ms': double.parse(naiveDurationMs.toStringAsFixed(3)),
    'memoized_duration_ms': double.parse(memoDurationMs.toStringAsFixed(4)),
    'speedup_factor': double.parse(speedup.toStringAsFixed(2)),
    'expected_result': memoRes,
    'actual_result': naiveRes,
    'correctness_verified': naiveRes == memoRes,
  };
}

Map<String, dynamic> runMonteCarloPi([int samples = 1000000]) {
  final rng = Random(999);
  int insideCount = 0;

  final stopwatch = Stopwatch()..start();
  for (int i = 0; i < samples; i++) {
    final double x = rng.nextDouble();
    final double y = rng.nextDouble();
    if (x * x + y * y <= 1.0) {
      insideCount++;
    }
  }
  stopwatch.stop();

  final double durationMs = stopwatch.elapsedMicroseconds / 1000.0;
  final double durationSec = durationMs / 1000.0;

  final double estimatedPi = 4.0 * (insideCount / samples);
  const double actualPi = pi;
  final double absError = (estimatedPi - actualPi).abs();
  final double samplesPerSec = samples / max(durationSec, 0.00001);

  return {
    'samples': samples,
    'estimated_pi': double.parse(estimatedPi.toStringAsFixed(6)),
    'actual_pi': double.parse(actualPi.toStringAsFixed(6)),
    'absolute_error': double.parse(absError.toStringAsFixed(6)),
    'duration_ms': double.parse(durationMs.toStringAsFixed(3)),
    'samples_per_sec': double.parse(samplesPerSec.toStringAsFixed(1)),
    'correctness_verified': absError < (samples < 100000 ? 0.05 : 0.01),
  };
}

Map<String, dynamic> executeAllBenchmarks({
  int datasetSize = 50000,
  int lookupKeys = 5000,
  int fibN = 30,
  int piSamples = 1000000,
}) {
  final stopwatch = Stopwatch()..start();

  final heapRes = runHeapSort(datasetSize);
  final hashRes = runHashTable(datasetSize * 2, lookupKeys);
  final fibRes = runFibonacci(fibN);
  final piRes = runMonteCarloPi(piSamples);

  stopwatch.stop();
  final double totalDurationMs = stopwatch.elapsedMicroseconds / 1000.0;

  return {
    'runtime': 'dart',
    'version': 'Dart ${Platform.version.split(' ').first}',
    'timestamp': DateTime.now().toUtc().toIso8601String(),
    'total_duration_ms': double.parse(totalDurationMs.toStringAsFixed(3)),
    'workloads': {
      'heap_sort': heapRes,
      'hash_table': hashRes,
      'fibonacci': fibRes,
      'monte_carlo_pi': piRes,
    },
  };
}

void main(List<String> args) {
  final bool isJson = args.contains('--json');

  int datasetSize = 50000;
  int lookupKeys = 5000;
  int fibN = 30;
  int piSamples = 1000000;

  for (int i = 0; i < args.length; i++) {
    if (args[i] == '--dataset' && i + 1 < args.length) {
      datasetSize = int.tryParse(args[i + 1]) ?? datasetSize;
    }
    if (args[i] == '--lookups' && i + 1 < args.length) {
      lookupKeys = int.tryParse(args[i + 1]) ?? lookupKeys;
    }
    if (args[i] == '--fib-n' && i + 1 < args.length) {
      fibN = int.tryParse(args[i + 1]) ?? fibN;
    }
    if (args[i] == '--samples' && i + 1 < args.length) {
      piSamples = int.tryParse(args[i + 1]) ?? piSamples;
    }
  }

  final result = executeAllBenchmarks(
    datasetSize: datasetSize,
    lookupKeys: lookupKeys,
    fibN: fibN,
    piSamples: piSamples,
  );

  if (isJson) {
    print(const JsonEncoder.withIndent('  ').convert(result));
  } else {
    print('Dart Algorithm Benchmarks (${result['version']}):');
    print('  • Heap Sort (${result['workloads']['heap_sort']['dataset_size']} items): ${result['workloads']['heap_sort']['duration_ms']} ms (Swaps: ${result['workloads']['heap_sort']['swaps']})');
    print('  • Hash Table (${result['workloads']['hash_table']['lookup_keys']} queries): ${result['workloads']['hash_table']['duration_ms']} ms (Avg: ${result['workloads']['hash_table']['avg_lookup_us']} µs/op)');
    print('  • Fibonacci (N=${result['workloads']['fibonacci']['n']}): ${result['workloads']['fibonacci']['naive_duration_ms']} ms (Speedup: ${result['workloads']['fibonacci']['speedup_factor']}x)');
    print('  • Monte Carlo Pi (${result['workloads']['monte_carlo_pi']['samples']} pts): ${result['workloads']['monte_carlo_pi']['duration_ms']} ms (Est: ${result['workloads']['monte_carlo_pi']['estimated_pi']}, Err: ${result['workloads']['monte_carlo_pi']['absolute_error']})');
    print('  Total Duration: ${result['total_duration_ms']} ms');
  }
}
