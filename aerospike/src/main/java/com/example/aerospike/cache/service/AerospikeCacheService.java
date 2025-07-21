package com.example.aerospike.cache.service;

import com.aerospike.client.AerospikeClient;
import com.aerospike.client.Bin;
import com.aerospike.client.Key;
import com.aerospike.client.Record;
import com.aerospike.client.policy.WritePolicy;
import com.example.aerospike.cache.config.AerospikeConfig;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;

/**
 * Service class for interacting with Aerospike cache
 */
@Slf4j
public class AerospikeCacheService {
    private static final String DATA_BIN = "data";
    private static final int DEFAULT_TTL = 3600; // 1 hour in seconds
    
    private final AerospikeClient client;
    private final String namespace;
    private final String set;
    private final ObjectMapper objectMapper;
    
    /**
     * Creates a new AerospikeCacheService with the given configuration
     * 
     * @param config Aerospike configuration
     */
    public AerospikeCacheService(AerospikeConfig config) {
        this.client = config.getClient();
        this.namespace = config.getNamespace();
        this.set = config.getSet();
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * Puts an object in the cache with the default TTL
     * 
     * @param key The cache key (integer)
     * @param value The object to cache
     * @param <T> The type of the object
     * @return true if successful, false otherwise
     */
    public <T> boolean put(Integer key, T value) {
        return put(key, value, DEFAULT_TTL);
    }
    
    /**
     * Puts an object in the cache with a custom TTL
     * 
     * @param key The cache key (integer)
     * @param value The object to cache
     * @param ttlSeconds Time-to-live in seconds
     * @param <T> The type of the object
     * @return true if successful, false otherwise
     */
    public <T> boolean put(Integer key, T value, int ttlSeconds) {
        try {
            String json = objectMapper.writeValueAsString(value);
            log.debug("Storing object with key={}, ttl={}: {}", key, ttlSeconds, json);
            
            Key asKey = new Key(namespace, set, key);
            Bin bin = new Bin(DATA_BIN, json);
            
            WritePolicy writePolicy = new WritePolicy();
            writePolicy.expiration = ttlSeconds;
            
            client.put(writePolicy, asKey, bin);
            return true;
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize object to JSON", e);
            return false;
        } catch (Exception e) {
            log.error("Failed to store object in cache", e);
            return false;
        }
    }
    
    /**
     * Gets an object from the cache
     * 
     * @param key The cache key (integer)
     * @param clazz The class of the object
     * @param <T> The type of the object
     * @return The cached object, or null if not found
     */
    public <T> T get(Integer key, Class<T> clazz) {
        try {
            Key asKey = new Key(namespace, set, key);
            Record record = client.get(null, asKey);
            
            if (record == null) {
                log.debug("Cache miss for key={}", key);
                return null;
            }
            
            String json = record.getString(DATA_BIN);
            if (json == null) {
                log.debug("No data found in bin for key={}", key);
                return null;
            }
            
            log.debug("Cache hit for key={}: {}", key, json);
            return objectMapper.readValue(json, clazz);
        } catch (IOException e) {
            log.error("Failed to deserialize JSON to object", e);
            return null;
        } catch (Exception e) {
            log.error("Failed to get object from cache", e);
            return null;
        }
    }
    
    /**
     * Deletes an object from the cache
     * 
     * @param key The cache key (integer)
     * @return true if successful, false otherwise
     */
    public boolean delete(Integer key) {
        try {
            Key asKey = new Key(namespace, set, key);
            client.delete(null, asKey);
            log.debug("Deleted object with key={}", key);
            return true;
        } catch (Exception e) {
            log.error("Failed to delete object from cache", e);
            return false;
        }
    }
    
    /**
     * Checks if an object exists in the cache
     * 
     * @param key The cache key (integer)
     * @return true if the object exists, false otherwise
     */
    public boolean exists(Integer key) {
        try {
            Key asKey = new Key(namespace, set, key);
            return client.exists(null, asKey);
        } catch (Exception e) {
            log.error("Failed to check if object exists in cache", e);
            return false;
        }
    }
    
    /**
     * Updates the TTL for an existing cache entry
     * 
     * @param key The cache key (integer)
     * @param ttlSeconds New time-to-live in seconds
     * @return true if successful, false otherwise
     */
    public boolean touch(Integer key, int ttlSeconds) {
        try {
            Key asKey = new Key(namespace, set, key);
            WritePolicy writePolicy = new WritePolicy();
            writePolicy.expiration = ttlSeconds;
            
            client.touch(writePolicy, asKey);
            log.debug("Updated TTL for key={} to {} seconds", key, ttlSeconds);
            return true;
        } catch (Exception e) {
            log.error("Failed to update TTL for object", e);
            return false;
        }
    }
}
