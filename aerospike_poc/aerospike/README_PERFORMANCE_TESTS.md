# Aerospike Performance Testing Framework

This document provides information about the performance testing framework for Aerospike in this project.

## Overview

The performance testing framework allows you to stress-test your Aerospike deployment with multiple parallel threads performing read operations. It provides detailed metrics on throughput, latency, and success rates.

## Available Tests

The framework includes several test scenarios:

1. **Uniform Read Test**: Each thread reads random records uniformly distributed across the dataset
2. **Hot Spot Read Test**: 80% of reads target 20% of the data (simulating real-world access patterns)
3. **Ramp-Up Test**: Gradually increases thread count to find the optimal concurrency level

## Running the Tests

There are multiple ways to run the performance tests:

### Option 1: Using the dedicated performance test demo

```bash
cd aerospike
./gradlew runPerformanceTests
```

This will execute all the test scenarios defined in `PerformanceTestDemo.java`.

### Option 2: Using the main demo application with "perf" argument

```bash
cd aerospike
./gradlew runPerformanceTestsFromDemo
```

This runs the main `AerospikeCacheDemo` application with the "perf" argument, which triggers the performance testing mode.

### Option 3: Running directly with Java

```bash
cd aerospike
java -Xmx2g -Xms1g -cp build/libs/aerospike-cache-poc-1.0-SNAPSHOT.jar com.example.aerospike.cache.AerospikeCacheDemo perf
```

This is useful if you want to customize the JVM arguments or run the tests in a production environment.

## Customizing Tests

To customize the tests, you can modify the `PerformanceTestDemo.java` file:

- Adjust thread counts
- Change test durations
- Modify key ranges
- Enable/disable latency measurements

For example, to run a custom test with 20 threads for 30 seconds:

```java
runCustomTest(cacheService, 20, 30);
```

## Test Parameters

When creating a performance tester, you can configure the following parameters:

- `threadCount`: Number of threads to use for testing
- `operationsPerThread`: Number of operations each thread should perform (0 for unlimited)
- `warmupOperations`: Number of warmup operations to perform before measuring
- `testDurationSeconds`: Maximum test duration in seconds (0 for unlimited)
- `minKey` and `maxKey`: Key range to use for reads
- `measureLatency`: Whether to measure and report latency statistics

## Understanding Results

The test results include:

### Throughput Metrics
- Operations per second (total throughput)
- Success rate (percentage of successful operations)

### Latency Metrics
- Average latency (ms)
- 50th percentile (median) latency (ms)
- 90th percentile latency (ms)
- 95th percentile latency (ms)
- 99th percentile latency (ms)
- Maximum latency (ms)

### CSV Export

The ramp-up test results are exported to a CSV file (`aerospike_rampup_results.csv`) that you can import into spreadsheet software or visualization tools for further analysis.

## Example Output

```
=== Uniform Read Test (10 threads, 10 seconds) ===
Starting uniform read test with 10 threads
Key range: 0 to 999999
Test completed in 10.05 seconds
Thread count: 10
Total operations: 245678
Successful operations: 245123
Failed operations: 555
Throughput: 24446.57 operations/second
Success rate: 99.77%
Latency statistics:
  Average: 0.41 ms
  50th percentile: 0.38 ms
  90th percentile: 0.62 ms
  95th percentile: 0.78 ms
  99th percentile: 1.25 ms
  Maximum: 12.45 ms
```

## Performance Tuning Tips

Based on the test results, you can tune your Aerospike deployment:

1. **Thread Count**: Find the optimal thread count where throughput is maximized without increasing latency too much
2. **Client Configuration**: Adjust client policies like timeouts and max connections
3. **Server Configuration**: Tune server parameters like service threads and transaction queues
4. **Network Settings**: Optimize network buffer sizes and connection limits
5. **Memory Allocation**: Ensure sufficient memory for both client and server

## Troubleshooting

If you encounter issues:

- Check that Aerospike server is running and accessible
- Verify that the key range matches the data you've inserted
- Increase JVM memory if you're testing with many threads or long durations
- Check Aerospike server logs for any errors or warnings
