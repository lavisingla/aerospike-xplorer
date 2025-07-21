package com.example.aerospike.cache;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.Info;
import com.aerospike.client.Key;
import com.aerospike.client.cluster.Node;
import com.aerospike.client.cluster.Partition;
import com.example.aerospike.cache.config.AerospikeConfig;
import com.example.aerospike.cache.model.Address;
import com.example.aerospike.cache.model.Security;
import com.example.aerospike.cache.model.User;
import com.example.aerospike.cache.perf.AerospikePerformanceTester;
import com.example.aerospike.cache.service.AerospikeCacheService;
import com.example.aerospike.cache.util.SecurityGenerator;

import lombok.extern.slf4j.Slf4j;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

/**
 * Demo application for Aerospike cache
 */
@Slf4j
public class AerospikeCacheDemo {

    public static void main(String[] args) {
        log.info("Starting Aerospike Cache Demo");
        
        // Initialize Aerospike configuration
        AerospikeConfig config = null;
        try {
            // Connect to the Aerospike cluster
            config = new AerospikeConfig();
            AerospikeClient client = config.getClient();
            
            // Display cluster information
            displayClusterInfo(client);
            
            // Initialize cache service
            AerospikeCacheService cacheService = new AerospikeCacheService(config);
            
            // Choose which operation to run
            if (args.length > 0 && "perf".equals(args[0])) {
                // Run performance tests
                runPerformanceTests(cacheService);
            } else {
                // Run regular demo
                displayClusterInfo(client);
                bulkOperation(cacheService);
                displayNamespaceStats(client, "test");
                // testReplication(cacheService);
            }
            
            log.info("Demo completed successfully");
        } catch (Exception e) {
            log.error("Demo failed", e);
        } finally {
            // Close Aerospike client
            if (config != null) {
                config.close();
                log.info("Aerospike client closed");
            }
        }
    }
    
    /**
     * Displays information about the Aerospike cluster
     */
    private static void displayClusterInfo(AerospikeClient client) {
        Node[] nodes = client.getNodes();
        log.info("Connected to Aerospike cluster with {} nodes:", nodes.length);
        
        for (Node node : nodes) {
            String nodeName = node.getName();
            String build = Info.request(node, "build");
            String edition = Info.request(node, "edition");
            String namespaces = Info.request(node, "namespaces");
            
            log.info("Node: {}", nodeName);
            log.info("  Build: {}", build);
            log.info("  Edition: {}", edition);
            log.info("  Namespaces: {}", namespaces);
        }
    }
    
    /**
     * Displays detailed namespace statistics including storage and memory usage
     * 
     * @param client The Aerospike client
     * @param namespace The namespace to get statistics for
     */
    public static void displayNamespaceStats(AerospikeClient client, String namespace) {
        log.info("=== Namespace Statistics for '{}' ===", namespace);
        
        if (client == null || client.getNodes().length == 0) {
            log.error("No Aerospike nodes available");
            return;
        }
        
        Node node = client.getNodes()[0]; // Using the first node for stats
        String stats = Info.request(node, "namespace/" + namespace);
        
        if (stats == null || stats.isEmpty()) {
            log.error("Failed to retrieve namespace statistics");
            return;
        }
        
        // Parse the statistics string into a map
        Map<String, String> statsMap = parseNameValueText(stats);
        
        // Extract and convert relevant metrics
        long dataUsedBytes = Long.parseLong(statsMap.getOrDefault("data-used-bytes", "0"));
        long dataTotalBytes = Long.parseLong(statsMap.getOrDefault("device-total-bytes", "0"));
        long indexUsedBytes = Long.parseLong(statsMap.getOrDefault("memory-used-bytes", "0"));
        long objects = Long.parseLong(statsMap.getOrDefault("objects", "0"));
        
        // Get memory usage from system statistics
        String systemStats = Info.request(node, "statistics");
        Map<String, String> systemStatsMap = parseNameValueText(systemStats);
        long heapUsedBytes = Long.parseLong(systemStatsMap.getOrDefault("heap_used_bytes", "0"));
        long heapTotalBytes = Long.parseLong(systemStatsMap.getOrDefault("heap_size", "0"));
        
        // Convert to MB for better readability
        double dataUsedMB = dataUsedBytes / (1024.0 * 1024.0);
        double dataTotalMB = dataTotalBytes / (1024.0 * 1024.0);
        double indexUsedMB = indexUsedBytes / (1024.0 * 1024.0);
        double heapUsedMB = heapUsedBytes / (1024.0 * 1024.0);
        double heapTotalMB = heapTotalBytes / (1024.0 * 1024.0);
        
        // Display the statistics
        log.info("Storage Usage:");
        log.info("  Data Used: {} MB / {} MB ({}%)", 
                String.format("%.2f", dataUsedMB), 
                String.format("%.2f", dataTotalMB), 
                String.format("%.2f", (dataUsedMB / dataTotalMB) * 100));
        log.info("  Index Used: {} MB", String.format("%.2f", indexUsedMB));
        log.info("  Total Objects: {}", objects);
        log.info("Memory Usage:");
        log.info("  Heap Used: {} MB / {} MB ({}%)", 
                String.format("%.2f", heapUsedMB), 
                String.format("%.2f", heapTotalMB), 
                String.format("%.2f", (heapUsedMB / heapTotalMB) * 100));
        
        // Additional useful statistics
        log.info("Additional Statistics:");
        log.info("  Master Objects: {}", statsMap.getOrDefault("master-objects", "0"));
        log.info("  Replication Factor: {}", statsMap.getOrDefault("replication-factor", "0"));
        log.info("  Memory Size: {} MB", 
                Long.parseLong(statsMap.getOrDefault("memory-size", "0")) / (1024 * 1024));
        log.info("  High Water Mark Disk Pct: {}%", statsMap.getOrDefault("high-water-disk-pct", "0"));
        log.info("  High Water Memory Pct: {}%", statsMap.getOrDefault("high-water-memory-pct", "0"));
        
        // Display any warnings or alerts
        boolean stopWrites = Boolean.parseBoolean(statsMap.getOrDefault("stop-writes", "false"));
        if (stopWrites) {
            log.warn("ALERT: Stop writes is enabled for this namespace!");
        }
        
        log.info("=== End of Namespace Statistics ===");
    }
    
    /**
     * Parses Aerospike name-value text format into a map
     * This is a utility method to replace the Info.parseNameValueText method
     * which may not be available in all Aerospike client versions
     * 
     * @param text The name-value text to parse (format: "name1=value1;name2=value2;...")
     * @return Map of name-value pairs
     */
    private static Map<String, String> parseNameValueText(String text) {
        Map<String, String> map = new HashMap<>();
        if (text == null || text.isEmpty()) {
            return map;
        }
        
        String[] pairs = text.split(";");
        for (String pair : pairs) {
            String[] nv = pair.split("=", 2);
            if (nv.length == 2) {
                map.put(nv[0], nv[1]);
            }
        }
        return map;
    }
    

    /**
     * Runs performance tests for Aerospike read operations
     * 
     * @param cacheService The Aerospike cache service to test
     */
    private static void runPerformanceTests(AerospikeCacheService cacheService) {
        log.info("Starting Aerospike performance tests");
        
        // Test configuration
        int minKey = 0;
        int maxKey = 999999; // Assuming 1 million records were inserted
        
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
        
        log.info("\n=== Extreme Load Test (50 threads, 20 seconds) ===");
        AerospikePerformanceTester extremeTester = AerospikePerformanceTester.builder()
                .threadCount(50)
                .operationsPerThread(0) // Unlimited operations per thread
                .warmupOperations(1000)
                .testDurationSeconds(20)
                .minKey(minKey)
                .maxKey(maxKey)
                .measureLatency(true)
                .cacheService(cacheService)
                .build();
        
        extremeTester.runUniformReadTest();
        
        log.info("Performance tests completed");
    }

    private static void testReplication(AerospikeCacheService cacheService) throws InterruptedException {
        Security sec = SecurityGenerator.generateRandomSecurity(123);
        cacheService.put(sec.getSpn(), sec);    
        // System.out.println("Inserted one row to aerospike");
        // System.out.println(cacheService.get(1760000, Security.class));
        // for (int i = 0; i < 120; i++) {
        //     Thread.sleep(1000);
        //     System.out.println(i);
        // }

        // for (int i = 0; i < 120; i++) {
        //     Thread.sleep(1000);
        //     Security s = cacheService.get(1760000, Security.class);
        //     if (s != null) {
        //         System.out.println("Cache value recieved = " +  s.getSpn());
        //     } else {
        //         System.out.println("No value recieved");;
        //     }
        // }
        long start = System.currentTimeMillis();
        while (true) {
            Security s = cacheService.get(123, Security.class);
            if (s == null) {
                System.out.println("No value recieved");
            }

            long end = System.currentTimeMillis();
            if (end - start > 60000) {
                break;
            }
        }
    }
    
    private static void bulkOperation(AerospikeCacheService cacheService) {
        final int startId = 0;
        final int endId = 100000;
        final int totalRecords = endId - startId;
        final int threadCount = 5;
        final int recordsPerThread = totalRecords / threadCount;
        
        log.info("Starting bulk operation with {} threads, {} records per thread", threadCount, recordsPerThread);
        
        // Create a fixed thread pool with 3 threads
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        
        // Create and submit tasks
        List<Future<?>> futures = new ArrayList<>();
        for (int t = 0; t < threadCount; t++) {
            final int threadStartId = startId + (t * recordsPerThread);
            final int threadEndId = (t == threadCount - 1) ? endId : threadStartId + recordsPerThread;
            
            futures.add(executor.submit(() -> {
                try {
                    log.debug("Thread {} processing records from {} to {}", 
                            Thread.currentThread().getName(), threadStartId, threadEndId);
                    
                    for (int i = threadStartId; i < threadEndId; i++) {
                        Security sec = SecurityGenerator.generateRandomSecurity(i);
                        
                        cacheService.put(sec.getSpn(), sec);
                        
                        // Optional: Add progress logging every 10,000 records
                        if (i % 10000 == 0) {
                            log.debug("Thread {} progress: inserted {} records", 
                                    Thread.currentThread().getName(), i - threadStartId);
                        }
                    }
                    
                    log.info("Thread {} completed", Thread.currentThread().getName());
                } catch (Exception e) {
                    log.error("Error in bulk operation thread: {}", e.getMessage(), e);
                }
            }));
        }
        
        // Wait for all tasks to complete
        for (Future<?> future : futures) {
            try {
                future.get();
            } catch (InterruptedException | ExecutionException e) {
                log.error("Error waiting for bulk operation to complete", e);
            }
        }
        
        // Shutdown the executor
        executor.shutdown();
        try {
            if (!executor.awaitTermination(1, TimeUnit.MINUTES)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
            Thread.currentThread().interrupt();
        }
        
        log.info("Bulk operation completed");
    }
}
