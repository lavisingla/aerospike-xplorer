package com.example.aerospike.cache.config;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Host;
import com.aerospike.client.policy.ClientPolicy;
import lombok.extern.slf4j.Slf4j;

import java.util.Arrays;

/**
 * Configuration class for Aerospike client
 */
@Slf4j
public class AerospikeConfig {
    // Default cluster configuration
    private static final Host[] DEFAULT_CLUSTER = new Host[] {
        new Host("34.28.68.126", 3000),  // aerospike1 service port
                new Host("34.133.17.182", 3010),  // aerospike service port
                        new Host("35.225.205.87", 3020)  // aerospike3 service port

    };
    private static final String DEFAULT_NAMESPACE = "test";  // Match the namespace in aerospike.conf
    private static final String DEFAULT_SET = "objects";
    
    private final AerospikeClient client;
    private final String namespace;
    private final String set;
    
    /**
     * Creates an Aerospike configuration with default cluster settings
     */
    public AerospikeConfig() {
        this(DEFAULT_CLUSTER, DEFAULT_NAMESPACE, DEFAULT_SET);
    }
    
    /**
     * Creates an Aerospike configuration with a single node
     * 
     * @param host Aerospike server host
     * @param port Aerospike server port
     * @param namespace Aerospike namespace
     * @param set Aerospike set name
     */
    public AerospikeConfig(String host, int port, String namespace, String set) {
        this(new Host[] { new Host(host, port) }, namespace, set);
    }
    
    /**
     * Creates an Aerospike configuration with cluster settings
     * 
     * @param hosts Array of Aerospike hosts in the cluster
     * @param namespace Aerospike namespace
     * @param set Aerospike set name
     */
    public AerospikeConfig(Host[] hosts, String namespace, String set) {
        log.info("Initializing Aerospike client with cluster={}, namespace={}, set={}", 
                Arrays.toString(hosts), namespace, set);
        
        ClientPolicy policy = new ClientPolicy();
        policy.timeout = 1000; // 1 second timeout
        policy.failIfNotConnected = true;
        
        try {
            this.client = new AerospikeClient(policy, hosts);
            this.namespace = namespace;
            this.set = set;
            log.info("Aerospike client initialized successfully with {} nodes", client.getNodes().length);
        } catch (Exception e) {
            log.error("Failed to initialize Aerospike client", e);
            throw new RuntimeException("Failed to initialize Aerospike client", e);
        }
    }
    
    /**
     * Gets the Aerospike client
     * 
     * @return AerospikeClient instance
     */
    public AerospikeClient getClient() {
        return client;
    }
    
    /**
     * Gets the namespace
     * 
     * @return namespace name
     */
    public String getNamespace() {
        return namespace;
    }
    
    /**
     * Gets the set name
     * 
     * @return set name
     */
    public String getSet() {
        return set;
    }
    
    /**
     * Closes the Aerospike client
     */
    public void close() {
        if (client != null && client.isConnected()) {
            log.info("Closing Aerospike client");
            client.close();
        }
    }
}
