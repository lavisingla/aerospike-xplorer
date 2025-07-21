package com.example.aerospike.cache.perf;

import com.example.aerospike.cache.config.AerospikeConfig;
import com.example.aerospike.cache.service.AerospikeCacheService;
import lombok.extern.slf4j.Slf4j;

import java.util.List;

/**
 * Demo class for running performance tests against Aerospike
 */
@Slf4j
public class PerformanceTestDemo {

    public static void main(String[] args) {
        log.info("Starting Aerospike Performance Test Demo");
        
        // Initialize Aerospike configuration
        AerospikeConfig config = null;
        try {
            // Connect to the Aerospike cluster
            config = new AerospikeConfig();
            
            // Initialize cache service
            AerospikeCacheService cacheService = new AerospikeCacheService(config);
            
            // Run performance tests
            runPerformanceTests(cacheService);
            
            log.info("Performance tests completed successfully");
        } catch (Exception e) {
            log.error("Performance tests failed", e);
        } finally {
            // Close Aerospike client
            if (config != null) {
                config.close();
                log.info("Aerospike client closed");
            }
        }
    }
    
    /**
     * Runs a series of performance tests
     */
    private static void runPerformanceTests(AerospikeCacheService cacheService) {
        // Test configuration
        int minKey = 0;
        int maxKey = 4999999; // Assuming 1 million records were inserted
        
        log.info("=== Uniform Read Test (10 threads, 10 seconds) ===");
        AerospikePerformanceTester uniformTester = AerospikePerformanceTester.builder()
                .threadCount(10)
                .operationsPerThread(0) // Unlimited operations per thread
                .warmupOperations(1000)
                .testDurationSeconds(10)
                .minKey(minKey)
                .maxKey(maxKey)
                .measureLatency(true)
                .cacheService(cacheService)
                .build();
        
        uniformTester.runUniformReadTest();

        log.info("=== Uniform Read Test (20 threads, 10 seconds) ===");
        AerospikePerformanceTester uniformTester2 = AerospikePerformanceTester.builder()
                .threadCount(20)
                .operationsPerThread(0) // Unlimited operations per thread
                .warmupOperations(1000)
                .testDurationSeconds(10)
                .minKey(minKey)
                .maxKey(maxKey)
                .measureLatency(true)
                .cacheService(cacheService)
                .build();
        
        uniformTester2.runUniformReadTest();
        
        log.info("\n=== Hot Spot Read Test (10 threads, 10 seconds) ===");
        AerospikePerformanceTester hotSpotTester = AerospikePerformanceTester.builder()
                .threadCount(10)
                .operationsPerThread(0) // Unlimited operations per thread
                .warmupOperations(1000)
                .testDurationSeconds(10)
                .minKey(minKey)
                .maxKey(maxKey)
                .measureLatency(true)
                .cacheService(cacheService)
                .build();
        
        hotSpotTester.runHotSpotReadTest();
        
        log.info("\n=== Ramp-Up Test (1 to 50 threads, 5 seconds per test) ===");
        AerospikePerformanceTester rampUpTester = AerospikePerformanceTester.builder()
                .threadCount(1) // Will be overridden in the ramp-up test
                .operationsPerThread(0) // Unlimited operations per thread
                .warmupOperations(500)
                .testDurationSeconds(5)
                .minKey(minKey)
                .maxKey(maxKey)
                .measureLatency(true)
                .cacheService(cacheService)
                .build();
        
        List<AerospikePerformanceTester.TestResult> rampUpResults = rampUpTester.runRampUpTest(50, 5);
        
        // Export results to CSV
        rampUpTester.exportResultsToCsv(rampUpResults, "aerospike_rampup_results.csv");
    }
    
    /**
     * Runs a custom performance test with the specified parameters
     */
    private static void runCustomTest(AerospikeCacheService cacheService, int threadCount, int durationSeconds) {
        log.info("=== Custom Read Test ({} threads, {} seconds) ===", threadCount, durationSeconds);
        
        AerospikePerformanceTester tester = AerospikePerformanceTester.builder()
                .threadCount(threadCount)
                .operationsPerThread(0) // Unlimited operations per thread
                .warmupOperations(1000)
                .testDurationSeconds(durationSeconds)
                .minKey(0)
                .maxKey(999999)
                .measureLatency(true)
                .cacheService(cacheService)
                .build();
        
        tester.runUniformReadTest();
    }
}
