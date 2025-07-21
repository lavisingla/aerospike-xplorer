# Aerospike Multi-Node Cluster with Monitoring

This project sets up a complete Aerospike multi-node cluster with AMC and Grafana monitoring using Docker Compose.

## Architecture

- **3-node Aerospike cluster** with mesh networking
- **SSD-based storage** (10GB total, ~3.33GB per node)
- **Full replication** across all nodes (replication factor = 3)
- **AMC (Aerospike Management Console)** for cluster management
- **Prometheus + Grafana** for advanced monitoring and visualization

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available for containers
- Ports 3000-3003, 3101-3103, 8081, 9090, 9145 available

## Quick Start

1. **Start the cluster:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for cluster formation (30-60 seconds):**
   ```bash
   docker-compose logs -f aerospike-1
   ```
   Look for "NODE-ID" and "CLUSTER-SIZE" messages indicating successful clustering.

3. **Verify cluster status:**
   ```bash
   docker exec aerospike-1 asadm -e "show statistics like cluster"
   ```

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **AMC (Aerospike Management Console)** | http://localhost:8081 | None required |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | None required |

### Aerospike Node Access
- **Node 1**: localhost:3001
- **Node 2**: localhost:3002  
- **Node 3**: localhost:3003

## Configuration Details

### Storage Configuration
- Each node has 2 namespaces: `test` and `bar`
- Each namespace uses 3GB of SSD storage per node
- Total cluster storage: ~18GB (with replication factor 3)
- Data is replicated across all 3 nodes

### Network Configuration
- **Service ports**: 3000 (mapped to 3001-3003 externally)
- **Heartbeat ports**: 3001 (for mesh clustering)
- **Fabric ports**: 3002 (for data migration)
- **Info ports**: 3003 (for monitoring)

## Monitoring

### AMC Features
- Real-time cluster monitoring
- Node health and performance metrics
- Namespace statistics
- Query performance analysis

### Grafana Dashboards
The setup includes a pre-configured dashboard showing:
- Objects per namespace
- Node uptime
- Memory usage per namespace
- Disk usage per namespace
- Read/Write success rates

## Management Commands

### Check Cluster Status
```bash
# View cluster information
docker exec aerospike-1 asadm -e "show statistics like cluster"

# View namespace information
docker exec aerospike-1 asadm -e "show statistics namespace"

# View node information
docker exec aerospike-1 asadm -e "show statistics service"
```

### Test Data Operations
```bash
# Insert test data
docker exec aerospike-1 aql -c "INSERT INTO test.demo (PK, name, age) VALUES ('key1', 'John', 25)"

# Query test data
docker exec aerospike-1 aql -c "SELECT * FROM test.demo WHERE PK='key1'"
```

### View Logs
```bash
# View all services
docker-compose logs -f

# View specific service
docker-compose logs -f aerospike-1
docker-compose logs -f grafana
docker-compose logs -f prometheus
```

## Scaling

To add more nodes to the cluster:

1. Add a new service in `docker-compose.yml`
2. Create a new configuration file in `aerospike/`
3. Update mesh-seed-address-port entries in all node configs
4. Restart the cluster

## Troubleshooting

### Cluster Formation Issues
```bash
# Check if nodes can see each other
docker exec aerospike-1 asadm -e "show statistics like cluster"

# Check heartbeat connectivity
docker-compose logs aerospike-1 | grep -i heartbeat
```

### Storage Issues
```bash
# Check namespace storage
docker exec aerospike-1 asadm -e "show statistics namespace"

# Check disk usage
docker exec aerospike-1 df -h /opt/aerospike/data
```

### Monitoring Issues
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check exporter metrics
curl http://localhost:9145/metrics
```

## Data Persistence

All data is stored in Docker volumes under `./volumes/`:
- `aerospike-data-1/`, `aerospike-data-2/`, `aerospike-data-3/`: Aerospike data
- `prometheus-data/`: Prometheus metrics data
- `grafana-data/`: Grafana configuration and dashboards

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove all data (WARNING: This will delete all stored data)
docker-compose down -v
sudo rm -rf volumes/
```

## Security Notes

- This setup is intended for development/testing
- Default credentials are used (Grafana: admin/admin)
- No authentication is configured for Aerospike
- Consider adding security measures for production use

## Support

For issues related to:
- **Aerospike**: Check [Aerospike Documentation](https://docs.aerospike.com/)
- **Docker**: Verify Docker and Docker Compose installation
- **Monitoring**: Check Prometheus and Grafana logs
