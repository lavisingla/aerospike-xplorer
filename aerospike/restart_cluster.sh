#!/bin/bash

echo "Stopping existing Aerospike containers..."
docker compose down

echo "Starting Aerospike cluster with new configuration..."
docker compose up -d

echo "Waiting for cluster to initialize (30 seconds)..."
sleep 30

echo "Checking cluster status..."
echo "Node 1 info:"
docker exec aerospike1 asinfo -v "status"
docker exec aerospike1 asinfo -v "tip:host=aerospike1;port=3002"
docker exec aerospike1 asinfo -v "tip:host=aerospike2;port=3002"
docker exec aerospike1 asinfo -v "tip:host=aerospike3;port=3002"

echo -e "\nNode 2 info:"
docker exec aerospike2 asinfo -v "status"

echo -e "\nNode 3 info:"
docker exec aerospike3 asinfo -v "status"

echo -e "\nCluster size:"
docker exec aerospike1 asinfo -v "cluster-size"

echo -e "\nCluster nodes:"
docker exec aerospike1 asadm -e "show config network"

echo -e "\nTo check the cluster in AMC, visit: http://localhost:8081"
echo "When connecting to AMC, use any of these addresses:"
echo "  - localhost:3001 (Node 1)"
echo "  - localhost:3002 (Node 2)"
echo "  - localhost:3003 (Node 3)"
