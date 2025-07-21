FROM aerospike/amc

# Install tzdata using apt
USER root
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

ENV TZ=UTC