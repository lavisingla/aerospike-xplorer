package com.example.aerospike.cache;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.Info;
import com.aerospike.client.cluster.Node;
import com.example.aerospike.cache.config.AerospikeConfig;
import com.example.aerospike.cache.model.Address;
import com.example.aerospike.cache.model.User;
import com.example.aerospike.cache.service.AerospikeCacheService;
import lombok.extern.slf4j.Slf4j;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
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
            
            // Run demo operations
            // demoBasicOperations(cacheService);
            // demoTtlOperations(cacheService);
            // demoNestedObjectOperations(cacheService);
            // demoClusterOperations(cacheService, client);
            bulkOperation(cacheService);
            
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
     * Demonstrates basic cache operations (put, get, delete)
     */
    private static void demoBasicOperations(AerospikeCacheService cacheService) {
        log.info("=== Basic Operations Demo ===");
        
        // Create a simple user
        User user = User.builder()
                .id(1)
                .name("John Doe")
                .email("john.doe@example.com")
                .build();
        
        // Store in cache
        boolean putResult = cacheService.put(user.getId(), user);
        log.info("Put result: {}", putResult);
        
        // Check if exists
        boolean existsResult = cacheService.exists(user.getId());
        log.info("Exists result: {}", existsResult);
        
        // Retrieve from cache
        User cachedUser = cacheService.get(user.getId(), User.class);
        log.info("Retrieved user: {}", cachedUser);
        
        // Delete from cache
        boolean deleteResult = cacheService.delete(user.getId());
        log.info("Delete result: {}", deleteResult);
        
        // Verify deletion
        boolean existsAfterDelete = cacheService.exists(user.getId());
        log.info("Exists after delete: {}", existsAfterDelete);
    }

    private static void bulkOperation(AerospikeCacheService cacheService) {
        for (int i = 0; i < 2000000; i++) {
            User user = User.builder()
                .id(i)
                .name("John Doe")
                .email("john.doe@example.com")
                .build();
        
        cacheService.put(user.getId(), user);

        }
    }
    
    /**
     * Demonstrates TTL operations
     */
    private static void demoTtlOperations(AerospikeCacheService cacheService) {
        log.info("=== TTL Operations Demo ===");
        
        // Create a simple user
        User user = User.builder()
                .id(2)
                .name("Jane Smith")
                .email("jane.smith@example.com")
                .build();
        
        // Store in cache with short TTL (5 seconds)
        boolean putResult = cacheService.put(user.getId(), user, 5);
        log.info("Put result with 5s TTL: {}", putResult);
        
        // Verify it exists
        boolean existsResult = cacheService.exists(user.getId());
        log.info("Exists immediately after put: {}", existsResult);
        
        // Wait for 3 seconds
        try {
            log.info("Waiting for 3 seconds...");
            TimeUnit.SECONDS.sleep(3);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        // Verify it still exists
        existsResult = cacheService.exists(user.getId());
        log.info("Exists after 3 seconds: {}", existsResult);
        
        // Update TTL to 10 more seconds
        boolean touchResult = cacheService.touch(user.getId(), 10);
        log.info("Touch result (extending TTL to 10s): {}", touchResult);
        
        // Wait for 6 more seconds (total 9 seconds)
        try {
            log.info("Waiting for 6 more seconds...");
            TimeUnit.SECONDS.sleep(6);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        // Verify it still exists after TTL extension
        existsResult = cacheService.exists(user.getId());
        log.info("Exists after TTL extension (9 seconds total): {}", existsResult);
        
        // Clean up
        cacheService.delete(user.getId());
    }
    
    /**
     * Demonstrates operations with nested objects
     */
    private static void demoNestedObjectOperations(AerospikeCacheService cacheService) {
        log.info("=== Nested Object Operations Demo ===");
        
        // Create address
        Address address = Address.builder()
                .street("123 Main St")
                .city("San Francisco")
                .state("CA")
                .zipCode("94105")
                .country("USA")
                .build();
        
        // Create orders
        List<User.Order> orders = Arrays.asList(
                User.Order.builder()
                        .orderId("ORD-001")
                        .productName("Laptop")
                        .price(1299.99)
                        .status("Delivered")
                        .build(),
                User.Order.builder()
                        .orderId("ORD-002")
                        .productName("Phone")
                        .price(799.99)
                        .status("Processing")
                        .build()
        );
        
        // Create attributes map
        Map<String, String> attributes = new HashMap<>();
        attributes.put("preference", "Electronics");
        attributes.put("membershipLevel", "Gold");
        
        // Create complex user with nested objects
        User complexUser = User.builder()
                .id(3)
                .name("Bob Johnson")
                .email("bob.johnson@example.com")
                .address(address)
                .phoneNumbers(Arrays.asList("555-1234", "555-5678"))
                .attributes(attributes)
                .orders(orders)
                .build();
        
        // Store in cache
        boolean putResult = cacheService.put(complexUser.getId(), complexUser);
        log.info("Put complex user result: {}", putResult);
        
        // Retrieve from cache
        User cachedComplexUser = cacheService.get(complexUser.getId(), User.class);
        log.info("Retrieved complex user: {}", cachedComplexUser);
        
        // Verify nested objects
        if (cachedComplexUser != null) {
            log.info("Address: {}", cachedComplexUser.getAddress());
            log.info("Phone numbers: {}", cachedComplexUser.getPhoneNumbers());
            log.info("Attributes: {}", cachedComplexUser.getAttributes());
            log.info("Orders: {}", cachedComplexUser.getOrders());
        }
        
        // Clean up
        cacheService.delete(complexUser.getId());
    }
    
    /**
     * Demonstrates cluster operations and high availability
     */
    private static void demoClusterOperations(AerospikeCacheService cacheService, AerospikeClient client) {
        log.info("=== Cluster Operations Demo ===");
        
        // Create test data with multiple keys
        for (int i = 100; i < 110; i++) {
            User user = User.builder()
                    .id(i)
                    .name("User " + i)
                    .email("user" + i + "@example.com")
                    .build();
            
            boolean putResult = cacheService.put(user.getId(), user);
            log.info("Put user {} result: {}", i, putResult);
        }
        
        // Display node distribution
        log.info("Data is distributed across {} nodes in the cluster", client.getNodes().length);
        
        // Demonstrate read operations from cluster
        log.info("Reading data from cluster...");
        for (int i = 100; i < 110; i++) {
            User user = cacheService.get(i, User.class);
            if (user != null) {
                log.info("Successfully read user {} from cluster: {}", i, user.getName());
            } else {
                log.error("Failed to read user {} from cluster", i);
            }
        }
        
        // Demonstrate high availability
        log.info("\nHigh Availability: Even if one node goes down, data remains accessible");
        log.info("In a production environment with replication-factor=2, data would still be");
        log.info("available if a node fails. The client automatically routes requests to available nodes.");
        
        // Clean up
        log.info("Cleaning up test data...");
        for (int i = 100; i < 110; i++) {
            cacheService.delete(i);
        }
    }
}
