#!/bin/bash
set -e

echo "Starting PostgreSQL container..."

# Ensure necessary build dependencies are installed
apt-get update && apt-get install -y \
    git \
    make \
    gcc \
    postgresql-server-dev-17 \
    build-essential

# Start PostgreSQL in the background to allow extensions to be installed
docker-entrypoint.sh postgres &

# Wait for PostgreSQL to be ready
until pg_isready -U "$DB_USERNAME" -d "$DB_DATABASE"; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done


echo "Installing pgvector extension..."
    
# Ensure clean environment
rm -rf /tmp/pgvector
    
# Clone and install pgvector
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector
cd /tmp/pgvector

make
make install

# Install extension
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "pgvector extension installed successfully."

# Bring PostgreSQL back to foreground
wait