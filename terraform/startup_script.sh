#!/bin/bash
set -e # Exit on error
set -x # Print commands

echo "Starting OpenFGA VM setup script..."

# Install dependencies
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release wget docker.io jq

# Ensure gcloud is available (usually pre-installed on Debian GCP images)
if ! command -v gcloud &>/dev/null; then
  echo "gcloud not found, installing..."
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
  apt-get update -y && apt-get install -y google-cloud-sdk
fi

# Get metadata values
DB_USER=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/db_user)
DB_NAME=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/db_name)
DB_INSTANCE_CONNECTION_NAME=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/db_instance_connection_name)
DB_PASSWORD_SECRET_NAME=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/db_password_secret_name)
DB_PASSWORD_SECRET_PROJECT_ID=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/db_password_secret_project_id)
DB_PASSWORD_SECRET_VERSION=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/db_password_secret_version) # Using specific version from TF
OPENFGA_IMAGE=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/openfga_image_name)
OPENFGA_PLAYGROUND_ENABLED=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/openfga_playground_setting)
OPENFGA_LOG_LEVEL=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/attributes/openfga_log_level)

echo "Fetching database password from Secret Manager..."
DB_PASSWORD=$(gcloud secrets versions access "${DB_PASSWORD_SECRET_VERSION}" --secret="${DB_PASSWORD_SECRET_NAME}" --project="${DB_PASSWORD_SECRET_PROJECT_ID}")
if [ -z "$DB_PASSWORD" ]; then
  echo "Failed to fetch DB password!"
  exit 1
fi

# Download and install Cloud SQL Auth Proxy
echo "Installing Cloud SQL Auth Proxy..."
wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.16.0/cloud-sql-proxy.linux.amd64 -O /usr/local/bin/cloud-sql-proxy
chmod +x /usr/local/bin/cloud-sql-proxy

OPENFGA_DSN="postgresql://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}?sslmode=disable"

# Pull OpenFGA Docker image
echo "Pulling OpenFGA image: ${OPENFGA_IMAGE}..."
docker pull ${OPENFGA_IMAGE}

# Stop and remove existing OpenFGA container if any (for script idempotency during testing)
docker stop openfga-server || true
docker rm openfga-server || true

# Run OpenFGA Docker container
echo "Starting cloud-sql-proxy..."
/usr/local/bin/cloud-sql-proxy $DB_INSTANCE_CONNECTION_NAME >/dev/null 2>&1 &

echo "Running DB migrations..."
docker run \
  --network host \
  -e OPENFGA_DATASTORE_ENGINE="postgres" \
  -e OPENFGA_DATASTORE_URI="${OPENFGA_DSN}" \
  -e OPENFGA_HTTP_ADDR=":8080" \
  -e OPENFGA_GRPC_ADDR=":8081" \
  -e OPENFGA_PLAYGROUND_ENABLED="${OPENFGA_PLAYGROUND_ENABLED}" \
  -e OPENFGA_PLAYGROUND_PORT="3000" \
  -e OPENFGA_LOG_LEVEL="${OPENFGA_LOG_LEVEL}" \
  ${OPENFGA_IMAGE} \
  migrate

echo "Migrations successfully ran. Starting openfga server..."
docker run -d --name openfga-server \
  --network host \
  -e OPENFGA_DATASTORE_ENGINE="postgres" \
  -e OPENFGA_DATASTORE_URI="${OPENFGA_DSN}" \
  -e OPENFGA_HTTP_ADDR=":8080" \
  -e OPENFGA_GRPC_ADDR=":8081" \
  -e OPENFGA_PLAYGROUND_ENABLED="${OPENFGA_PLAYGROUND_ENABLED}" \
  -e OPENFGA_PLAYGROUND_PORT="3000" \
  -e OPENFGA_LOG_LEVEL="${OPENFGA_LOG_LEVEL}" \
  --restart always \
  ${OPENFGA_IMAGE} \
  run

echo "OpenFGA container started."
echo "OpenFGA VM setup script finished successfully."
