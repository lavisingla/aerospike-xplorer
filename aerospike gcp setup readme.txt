Install aerospike on any instance
1. wget -O - https://artifacts.aerospike.com/aerospike-server-community/7.0.0/aerospike-server-community_7.0.0.25_tools-10.2.1_ubuntu22.04_x86_64.tgz | tar -xz
2. cd aerospike-server-community-7.0.0.0-ubuntu22.04
3. sudo ./asinstall

sudo systemctl enable aerospike
sudo systemctl start aerospike

sudo systemctl restart aerospike
sudo systemctl status aerospike

run on new nodes to free up ssd for aerospike
sudo dd if=/dev/zero of=/dev/sdb bs=1M count=10


You can now check if nodes are connected using:
asadm -e info

create log file
sudo mkdir /var/log/aerospike


AMC
docker run -d \
  --name aerospike-amc \
  --restart always \
  -p 8081:8081 \
  -v /etc/localtime:/etc/localtime:ro \
  -v /usr/share/zoneinfo:/usr/share/zoneinfo:ro \
  -e TZ=Etc/GMT \
  aerospike/amc:latest
  
  
node exporter on a aerospike node instance

# Download and install latest Node Exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.9.1/node_exporter-1.9.1.linux-amd64.tar.gz
tar -xzf node_exporter-1.9.1.linux-amd64.tar.gz
sudo cp node_exporter-1.9.1.linux-amd64/node_exporter /usr/local/bin/

# Create a systemd service
sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=nobody
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=default.target
EOF

# Start and enable the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
sudo systemctl status node_exporter




-- restart aerospike
sudo systemctl stop aerospike
sudo blkdiscard /dev/sdb
sudo systemctl start aerospike
sudo systemctl status aerospike
asadm -e info

