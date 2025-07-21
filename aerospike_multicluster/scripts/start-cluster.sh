#!/bin/bash

# Aerospike Multi-Node Cluster Startup Script

set -e

echo "🚀 Starting Aerospike Multi-Node Cluster with Monitoring..."

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Create necessary directories
echo "📁 Creating volume directories..."
mkdir -p volumes/aerospike-data-1
mkdir -p volumes/aerospike-data-2
mkdir -p volumes/aerospike-data-3
mkdir -p volumes/prometheus-data
mkdir -p volumes/grafana-data

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 volumes/aerospike-data-*
chmod 755 volumes/prometheus-data
chmod 755 volumes/grafana-data

# Start the cluster
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Wait for Aerospike nodes to be ready
echo "🔍 Checking Aerospike node status..."
for i in {1..30}; do
    if docker exec aerospike-1 asinfo -v "status" &>/dev/null; then
        echo "✅ Aerospike Node 1 is ready"
        break
    fi
    echo "⏳ Waiting for Aerospike Node 1... ($i/30)"
    sleep 2
done

# Wait a bit more for cluster formation
echo "⏳ Waiting for cluster formation..."
sleep 15

# Check cluster status
echo "📊 Checking cluster status..."
if docker exec aerospike-1 asadm -e "show statistics like cluster" 2>/dev/null; then
    echo "✅ Cluster is formed successfully!"
else
    echo "⚠️  Cluster might still be forming. Check logs with: docker-compose logs -f"
fi

# Display access information
echo ""
echo "🎉 Aerospike Multi-Node Cluster is starting up!"
echo ""
echo "📋 Access Points:"
echo "   AMC (Management Console): http://localhost:8081"
echo "   Grafana (Monitoring):     http://localhost:3000 (admin/admin)"
echo "   Prometheus:               http://localhost:9090"
echo ""
echo "🔧 Aerospike Nodes:"
echo "   Node 1: localhost:3001"
echo "   Node 2: localhost:3002"
echo "   Node 3: localhost:3003"
echo ""
echo "📝 Useful Commands:"
echo "   Check cluster status:     docker exec aerospike-1 asadm -e 'show statistics like cluster'"
echo "   View logs:                docker-compose logs -f"
echo "   Stop cluster:             docker-compose down"
echo ""
echo "📖 For more information, see README.md"
