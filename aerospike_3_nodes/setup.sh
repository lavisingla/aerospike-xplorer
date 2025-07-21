#!/bin/bash

# Create data directories for Aerospike nodes
mkdir -p data/aerospike-1
mkdir -p data/aerospike-2
mkdir -p data/aerospike-3

# Set permissions
chmod -R 777 data/

echo "Directory structure created."
echo "To start the Aerospike cluster, run: docker-compose up -d"
echo "To access AMC (Aerospike Management Console), open: http://localhost:8081"
echo "To check cluster status, run: docker exec aerospike-1 asadm -e 'info'"
echo "To stop the cluster, run: docker-compose down"
