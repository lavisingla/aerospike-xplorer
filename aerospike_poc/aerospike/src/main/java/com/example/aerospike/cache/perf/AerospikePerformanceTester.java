package com.example.aerospike.cache.perf;

import com.example.aerospike.cache.config.AerospikeConfig;
import com.example.aerospike.cache.model.Security;
import com.example.aerospike.cache.service.AerospikeCacheService;
import lombok.Builder;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;

import java.io.FileWriter;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * Performance testing framework for Aerospike cache operations
 */
@Slf4j
public class AerospikePerformanceTester {
    
    // Test configuration
    private final int threadCount;
    private final int operationsPerThread;
    private final int warmupOperations;
    private final int testDurationSeconds;
    private final int minKey;
    private final int maxKey;
    private final boolean measureLatency;
    
    // Services
    private final AerospikeCacheService cacheService;
    
    // Performance metrics
    private final AtomicLong totalOperations = new AtomicLong(0);
    private final AtomicLong successfulOperations = new AtomicLong(0);
    private final AtomicLong failedOperations = new AtomicLong(0);
    private final ConcurrentLinkedQueue<Long> latencies = new ConcurrentLinkedQueue<>();
    
    // Random number generator
    private final Random random = new Random();
    
    /**
     * Creates a new performance tester with the specified configuration
     * 
     * @param threadCount Number of threads to use for testing
     * @param operationsPerThread Number of operations each thread should perform (0 for unlimited)
     * @param warmupOperations Number of warmup operations to perform before measuring
     * @param testDurationSeconds Maximum test duration in seconds (0 for unlimited)
     * @param minKey Minimum key value to use for reads
     * @param maxKey Maximum key value to use for reads
     * @param measureLatency Whether to measure and report latency statistics
     * @param cacheService The Aerospike cache service to test
     */
    @Builder
    public AerospikePerformanceTester(
            int threadCount,
            int operationsPerThread,
            int warmupOperations,
            int testDurationSeconds,
            int minKey,
            int maxKey,
            boolean measureLatency,
            AerospikeCacheService cacheService) {
        
        this.threadCount = threadCount;
        this.operationsPerThread = operationsPerThread;
        this.warmupOperations = warmupOperations;
        this.testDurationSeconds = testDurationSeconds;
        this.minKey = minKey;
        this.maxKey = maxKey;
        this.measureLatency = measureLatency;
        this.cacheService = cacheService;
    }
    
    /**
     * Runs a uniform read test where keys are selected randomly with uniform distribution
     */
    public TestResult runUniformReadTest() {
        log.info("Starting uniform read test with {} threads", threadCount);
        log.info("Key range: {} to {}", minKey, maxKey);
        
        // Reset metrics
        resetMetrics();
        
        // Create thread pool
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        CountDownLatch latch = new CountDownLatch(threadCount);
        
        // Start time
        Instant startTime = Instant.now();
        
        // Submit tasks
        for (int i = 0; i < threadCount; i++) {
            executor.submit(() -> {
                try {
                    runUniformReadWorker();
                } finally {
                    latch.countDown();
                }
            });
        }
        
        // Wait for completion
        try {
            boolean completed = latch.await(testDurationSeconds > 0 ? testDurationSeconds : Long.MAX_VALUE, TimeUnit.SECONDS);
            if (!completed) {
                log.info("Test duration limit reached, stopping test");
            }
        } catch (InterruptedException e) {
            log.error("Test interrupted", e);
            Thread.currentThread().interrupt();
        }
        
        // End time
        Instant endTime = Instant.now();
        Duration duration = Duration.between(startTime, endTime);
        
        // Shutdown executor
        executor.shutdownNow();
        
        // Calculate results
        TestResult result = calculateResults(duration);
        
        // Print results
        printResults(result);
        
        return result;
    }
    
    /**
     * Runs a hot spot read test where 80% of reads target 20% of the data
     */
    public TestResult runHotSpotReadTest() {
        log.info("Starting hot spot read test with {} threads", threadCount);
        log.info("Key range: {} to {}", minKey, maxKey);
        log.info("80% of reads will target 20% of the data");
        
        // Reset metrics
        resetMetrics();
        
        // Create thread pool
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        CountDownLatch latch = new CountDownLatch(threadCount);
        
        // Calculate hot spot range (20% of keys)
        int hotSpotSize = (int)((maxKey - minKey + 1) * 0.2);
        int hotSpotStart = minKey + random.nextInt(maxKey - minKey - hotSpotSize + 1);
        int hotSpotEnd = hotSpotStart + hotSpotSize - 1;
        
        log.info("Hot spot range: {} to {}", hotSpotStart, hotSpotEnd);
        
        // Start time
        Instant startTime = Instant.now();
        
        // Submit tasks
        for (int i = 0; i < threadCount; i++) {
            final int threadId = i;
            executor.submit(() -> {
                try {
                    runHotSpotReadWorker(hotSpotStart, hotSpotEnd);
                } finally {
                    latch.countDown();
                }
            });
        }
        
        // Wait for completion
        try {
            boolean completed = latch.await(testDurationSeconds > 0 ? testDurationSeconds : Long.MAX_VALUE, TimeUnit.SECONDS);
            if (!completed) {
                log.info("Test duration limit reached, stopping test");
            }
        } catch (InterruptedException e) {
            log.error("Test interrupted", e);
            Thread.currentThread().interrupt();
        }
        
        // End time
        Instant endTime = Instant.now();
        Duration duration = Duration.between(startTime, endTime);
        
        // Shutdown executor
        executor.shutdownNow();
        
        // Calculate results
        TestResult result = calculateResults(duration);
        
        // Print results
        printResults(result);
        
        return result;
    }
    
    /**
     * Runs a ramp-up test with increasing thread counts
     */
    public List<TestResult> runRampUpTest(int maxThreads, int threadsStep) {
        log.info("Starting ramp-up test from 1 to {} threads (step: {})", maxThreads, threadsStep);
        
        List<TestResult> results = new ArrayList<>();
        
        for (int threads = 1; threads <= maxThreads; threads += threadsStep) {
            log.info("Testing with {} threads", threads);
            
            // Create a new tester with the current thread count
            AerospikePerformanceTester tester = AerospikePerformanceTester.builder()
                    .threadCount(threads)
                    .operationsPerThread(this.operationsPerThread)
                    .warmupOperations(this.warmupOperations)
                    .testDurationSeconds(this.testDurationSeconds)
                    .minKey(this.minKey)
                    .maxKey(this.maxKey)
                    .measureLatency(this.measureLatency)
                    .cacheService(this.cacheService)
                    .build();
            
            // Run the test
            TestResult result = tester.runUniformReadTest();
            results.add(result);
            
            // Short pause between tests
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        
        // Print summary
        log.info("Ramp-up test summary:");
        log.info("Threads | Throughput (ops/s) | Avg Latency (ms) | Success Rate (%)");
        log.info("--------|-------------------|------------------|----------------");
        
        for (TestResult result : results) {
            log.info(String.format("%-8d| %-19.2f| %-18.2f| %.2f%%",
                    result.getThreadCount(),
                    result.getThroughput(),
                    result.getAvgLatencyMs(),
                    result.getSuccessRate() * 100));
        }
        
        return results;
    }
    
    /**
     * Exports test results to a CSV file
     */
    public void exportResultsToCsv(List<TestResult> results, String filename) {
        try (FileWriter writer = new FileWriter(filename)) {
            // Write header
            writer.write("Threads,Throughput (ops/s),Avg Latency (ms),P50 Latency (ms),P90 Latency (ms)," +
                    "P95 Latency (ms),P99 Latency (ms),Max Latency (ms),Success Rate (%)\n");
            
            // Write data
            for (TestResult result : results) {
                writer.write(String.format("%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
                        result.getThreadCount(),
                        result.getThroughput(),
                        result.getAvgLatencyMs(),
                        result.getP50LatencyMs(),
                        result.getP90LatencyMs(),
                        result.getP95LatencyMs(),
                        result.getP99LatencyMs(),
                        result.getMaxLatencyMs(),
                        result.getSuccessRate() * 100));
            }
            
            log.info("Results exported to {}", filename);
        } catch (IOException e) {
            log.error("Failed to export results to CSV", e);
        }
    }
    
    /**
     * Worker method for uniform read test
     */
    private void runUniformReadWorker() {
        int opsCount = 0;
        boolean unlimited = operationsPerThread <= 0;
        Instant endTime = testDurationSeconds > 0 ? 
                Instant.now().plusSeconds(testDurationSeconds) : Instant.MAX;
        
        // Perform warmup operations
        for (int i = 0; i < warmupOperations; i++) {
            int key = minKey + random.nextInt(maxKey - minKey + 1);
            cacheService.get(key, Security.class);
        }
        
        // Perform test operations
        while ((unlimited || opsCount < operationsPerThread) && Instant.now().isBefore(endTime)) {
            int key = minKey + random.nextInt(maxKey - minKey + 1);
            
            Instant start = measureLatency ? Instant.now() : null;
            
            try {
                Security security = cacheService.get(key, Security.class);
                if (security != null) {
                    successfulOperations.incrementAndGet();
                } else {
                    failedOperations.incrementAndGet();
                }
            } catch (Exception e) {
                failedOperations.incrementAndGet();
            }
            
            if (measureLatency) {
                long latencyNanos = Duration.between(start, Instant.now()).toNanos();
                latencies.add(latencyNanos);
            }
            
            totalOperations.incrementAndGet();
            opsCount++;
        }
    }
    
    /**
     * Worker method for hot spot read test
     */
    private void runHotSpotReadWorker(int hotSpotStart, int hotSpotEnd) {
        int opsCount = 0;
        boolean unlimited = operationsPerThread <= 0;
        Instant endTime = testDurationSeconds > 0 ? 
                Instant.now().plusSeconds(testDurationSeconds) : Instant.MAX;
        
        // Perform warmup operations
        for (int i = 0; i < warmupOperations; i++) {
            int key = getHotSpotKey(hotSpotStart, hotSpotEnd);
            cacheService.get(key, Security.class);
        }
        
        // Perform test operations
        while ((unlimited || opsCount < operationsPerThread) && Instant.now().isBefore(endTime)) {
            int key = getHotSpotKey(hotSpotStart, hotSpotEnd);
            
            Instant start = measureLatency ? Instant.now() : null;
            
            try {
                Security security = cacheService.get(key, Security.class);
                if (security != null) {
                    successfulOperations.incrementAndGet();
                } else {
                    failedOperations.incrementAndGet();
                }
            } catch (Exception e) {
                failedOperations.incrementAndGet();
            }
            
            if (measureLatency) {
                long latencyNanos = Duration.between(start, Instant.now()).toNanos();
                latencies.add(latencyNanos);
            }
            
            totalOperations.incrementAndGet();
            opsCount++;
        }
    }
    
    /**
     * Gets a key using the hot spot distribution (80% chance of hot spot, 20% chance of cold spot)
     */
    private int getHotSpotKey(int hotSpotStart, int hotSpotEnd) {
        if (random.nextDouble() < 0.8) {
            // Hot spot (80% of requests)
            return hotSpotStart + random.nextInt(hotSpotEnd - hotSpotStart + 1);
        } else {
            // Cold spot (20% of requests)
            int key;
            do {
                key = minKey + random.nextInt(maxKey - minKey + 1);
            } while (key >= hotSpotStart && key <= hotSpotEnd);
            return key;
        }
    }
    
    /**
     * Resets all metrics
     */
    private void resetMetrics() {
        totalOperations.set(0);
        successfulOperations.set(0);
        failedOperations.set(0);
        latencies.clear();
    }
    
    /**
     * Calculates test results
     */
    private TestResult calculateResults(Duration duration) {
        double durationSeconds = duration.toMillis() / 1000.0;
        double throughput = totalOperations.get() / durationSeconds;
        double successRate = totalOperations.get() > 0 ? 
                (double) successfulOperations.get() / totalOperations.get() : 0;
        
        // Calculate latency percentiles
        double avgLatencyMs = 0;
        double p50LatencyMs = 0;
        double p90LatencyMs = 0;
        double p95LatencyMs = 0;
        double p99LatencyMs = 0;
        double maxLatencyMs = 0;
        
        if (measureLatency && !latencies.isEmpty()) {
            List<Long> sortedLatencies = new ArrayList<>(latencies);
            Collections.sort(sortedLatencies);
            
            // Convert from nanos to millis
            avgLatencyMs = sortedLatencies.stream().mapToLong(Long::longValue).average().orElse(0) / 1_000_000.0;
            p50LatencyMs = getPercentile(sortedLatencies, 50) / 1_000_000.0;
            p90LatencyMs = getPercentile(sortedLatencies, 90) / 1_000_000.0;
            p95LatencyMs = getPercentile(sortedLatencies, 95) / 1_000_000.0;
            p99LatencyMs = getPercentile(sortedLatencies, 99) / 1_000_000.0;
            maxLatencyMs = sortedLatencies.get(sortedLatencies.size() - 1) / 1_000_000.0;
        }
        
        return TestResult.builder()
                .threadCount(threadCount)
                .totalOperations(totalOperations.get())
                .successfulOperations(successfulOperations.get())
                .failedOperations(failedOperations.get())
                .durationSeconds(durationSeconds)
                .throughput(throughput)
                .successRate(successRate)
                .avgLatencyMs(avgLatencyMs)
                .p50LatencyMs(p50LatencyMs)
                .p90LatencyMs(p90LatencyMs)
                .p95LatencyMs(p95LatencyMs)
                .p99LatencyMs(p99LatencyMs)
                .maxLatencyMs(maxLatencyMs)
                .build();
    }
    
    /**
     * Gets a percentile value from a sorted list
     */
    private double getPercentile(List<Long> sortedValues, int percentile) {
        if (sortedValues.isEmpty()) {
            return 0;
        }
        
        int index = (int) Math.ceil(percentile / 100.0 * sortedValues.size()) - 1;
        return sortedValues.get(Math.max(0, index));
    }
    
    /**
     * Prints test results
     */
    private void printResults(TestResult result) {
        log.info("Test completed in {} seconds - ",  result.getDurationSeconds());
        log.info("Thread count: {}", result.getThreadCount());
        log.info("Total operations: {}", result.getTotalOperations());
        log.info("Successful operations: {}", result.getSuccessfulOperations());
        log.info("Failed operations: {}", result.getFailedOperations());
        log.info("Throughput: {} operations/second", result.getThroughput());
        log.info("Success rate: {}%", result.getSuccessRate() * 100);
        
        if (measureLatency) {
            log.info("Latency statistics:");
            log.info("  Average: {} ms", result.getAvgLatencyMs());
            log.info("  50th percentile: {} ms", result.getP50LatencyMs());
            log.info("  90th percentile: {} ms", result.getP90LatencyMs());
            log.info("  95th percentile: {} ms", result.getP95LatencyMs());
            log.info("  99th percentile: {} ms", result.getP99LatencyMs());
            log.info("  Maximum: {} ms", result.getMaxLatencyMs());
        }
    }
    
    /**
     * Test result data class
     */
    @Data
    @Builder
    public static class TestResult {
        private int threadCount;
        private long totalOperations;
        private long successfulOperations;
        private long failedOperations;
        private double durationSeconds;
        private double throughput;
        private double successRate;
        private double avgLatencyMs;
        private double p50LatencyMs;
        private double p90LatencyMs;
        private double p95LatencyMs;
        private double p99LatencyMs;
        private double maxLatencyMs;
    }
}
