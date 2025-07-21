# Aerospike Cache POC

This project demonstrates how to use Aerospike as a cache database for Java applications, with a focus on caching nested Java objects by converting them to JSON. It includes both single-node and cluster configurations.

## Features

- Docker-based Aerospike setup (single node or cluster)
- Java client for Aerospike with cluster support
- JSON serialization/deserialization of nested Java objects
- TTL-based cache expiration
- Basic cache operations (put, get, delete, exists)
- High availability with multi-node cluster

## Prerequisites

- Docker and Docker Compose
- Java 11 or higher
- Maven

## Project Structure

```
aerospike-cache-poc/
├── docker-compose.yml        # Docker Compose configuration
├── aerospike.conf            # Aerospike server configuration
├── pom.xml                   # Maven project configuration
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/aerospike/cache/
│   │   │       ├── config/
│   │   │       │   └── AerospikeConfig.java       # Aerospike client configuration
│   │   │       ├── model/
│   │   │       │   ├── Address.java               # Sample nested object
│   │   │       │   └── User.java                  # Sample complex object with nesting
│   │   │       ├── service/
│   │   │       │   └── AerospikeCacheService.java # Cache service implementation
│   │   │       └── AerospikeCacheDemo.java        # Demo application
│   │   └── resources/
│   │       └── logback.xml                        # Logging configuration
```

## Getting Started

### 1. Start Aerospike Server

For a single node setup:
```bash
docker compose up -d
```

For a cluster setup:
```bash
docker compose up -d aerospike1 aerospike2 aerospike3 amc
```

This will start Aerospike server(s) with the configuration specified in the respective `aerospike.conf` files. The cluster setup includes the Aerospike Management Console (AMC) accessible at http://localhost:8081.

### 2. Build the Project

```bash
# Using Gradle
./gradlew build

# Using Maven (legacy)
mvn clean package
```

### 3. Run the Demo

```bash
# Using Gradle
./gradlew runDemo

# Using Maven (legacy)
mvn exec:java
```

This will run the `AerospikeCacheDemo` class, which demonstrates:
- Basic cache operations (put, get, delete)
- TTL operations (expiration and extension)
- Nested object operations (storing and retrieving complex objects)

## Configuration

### Aerospike Server Configuration

#### Single Node Setup
The `aerospike.conf` file contains the Aerospike server configuration:
- Uses SSD storage engine to minimize RAM usage
- Configures a namespace called "cache"
- Sets default TTL to 30 days
- Enables compression to save space

#### Cluster Setup
The cluster configuration uses three nodes with mesh heartbeat for node discovery:
- Each node has its own configuration file (`node1/aerospike.conf`, `node2/aerospike.conf`, `node3/aerospike.conf`)
- Uses in-memory storage for fast cache access
- Configures a namespace called "test" with replication factor 2
- Sets default TTL to 30 days
- Nodes communicate with each other via mesh heartbeat configuration

### Java Client Configuration

The `AerospikeConfig` class configures the Java client:

#### Single Node Configuration
- Default host: localhost
- Default port: 3000
- Default namespace: cache
- Default set: objects

#### Cluster Configuration
- Multiple hosts: localhost:3001, localhost:3002, localhost:3003
- Default namespace: test (matching the cluster configuration)
- Default set: objects
- Automatic connection to all available nodes

## Cache Service

The `AerospikeCacheService` class provides methods for:
- Storing objects in the cache (`put`)
- Retrieving objects from the cache (`get`)
- Checking if objects exist in the cache (`exists`)
- Deleting objects from the cache (`delete`)
- Updating TTL for cache entries (`touch`)

## Storage Model

This POC supports two storage models:

### Single Node with SSD
- SSD storage engine to minimize RAM usage
- Single bin JSON storage (entire object stored as JSON in a single bin)
- Integer keys for efficient lookups

### Cluster with In-Memory
- In-memory storage for fast access
- Replication factor of 2 for high availability
- Single bin JSON storage (entire object stored as JSON in a single bin)
- Integer keys for efficient lookups

## Customization

To customize the cache behavior:
- Modify `aerospike.conf` for server-side settings
- Modify `AerospikeConfig` for client-side settings
- Modify `AerospikeCacheService` for cache operations

## Shutting Down

For single node or cluster:
```bash
docker compose down
```

This will stop and remove all Aerospike containers.

## Cluster Management

### Restarting the Cluster

We've provided a script to restart the Aerospike cluster and verify that all nodes are forming a single cluster:

```bash
./restart_cluster.sh
```

This script will:
1. Stop any existing Aerospike containers
2. Start the cluster with the new configuration
3. Wait for the cluster to initialize
4. Display cluster status information

### Monitoring the Cluster

You can access the Aerospike Management Console (AMC) at http://localhost:8081 to:
- Monitor cluster health
- View node statistics
- Manage namespaces and sets
- Monitor replication status

When connecting to AMC, you can use any of these addresses:
- localhost:3001 (Node 1)
- localhost:3002 (Node 2)
- localhost:3003 (Node 3)

### Troubleshooting Cluster Formation

If you're experiencing issues with cluster formation:

1. **Check container connectivity**:
   ```bash
   docker exec aerospike1 ping -c 2 aerospike2
   docker exec aerospike1 ping -c 2 aerospike3
   ```

2. **Verify heartbeat ports**:
   ```bash
   docker exec aerospike1 netstat -an | grep 3002
   ```

3. **Check cluster status**:
   ```bash
   docker exec aerospike1 asinfo -v "cluster-size"
   ```

4. **View logs**:
   ```bash
   docker logs aerospike1
   ```
