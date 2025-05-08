provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable necessary APIs
resource "google_project_service" "compute_api" {
  project            = var.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin_api" {
  project            = var.project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam_api" {
  project            = var.project_id
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager_api" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Random password for the database user
resource "random_password" "db_password" {
  length  = 20
  special = false
}

# Store the database password in Secret Manager
resource "google_secret_manager_secret" "db_password_secret" {
  project   = var.project_id
  secret_id = "${var.cloud_sql_instance_name}-db-password" # This is the short name

  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "db_password_secret_version" {
  secret      = google_secret_manager_secret.db_password_secret.id # Full ID: projects/.../secrets/...
  secret_data = random_password.db_password.result
}

# Cloud SQL Postgres Instance
resource "google_sql_database_instance" "main" {
  project             = var.project_id
  name                = var.cloud_sql_instance_name
  region              = var.region
  database_version    = "POSTGRES_14"
  deletion_protection = false

  settings {
    tier = var.cloud_sql_tier
    ip_configuration {
      ipv4_enabled = true # Required for Cloud SQL Proxy from GCE by default
    }
  }
  depends_on = [google_project_service.sqladmin_api]
}

# Database within the Cloud SQL instance
resource "google_sql_database" "openfga_db" {
  project  = var.project_id
  name     = var.cloud_sql_db_name
  instance = google_sql_database_instance.main.name
}

# User for OpenFGA to connect to the database
resource "google_sql_user" "openfga_user" {
  project  = var.project_id
  name     = var.cloud_sql_user_name
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

# Service Account for GCE Instance
resource "google_service_account" "gce_sa" {
  project      = var.project_id
  account_id   = substr("openfga-gce-sa-${random_password.db_password.id}", 0, 30) # Ensure unique & valid account_id
  display_name = "OpenFGA GCE Service Account"
}

# Grant GCE SA permission to access the Secret
resource "google_secret_manager_secret_iam_member" "gce_sa_db_password_accessor" {
  project   = google_secret_manager_secret.db_password_secret.project
  secret_id = google_secret_manager_secret.db_password_secret.secret_id # Short name of the secret
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gce_sa.email}"

  depends_on = [
    google_secret_manager_secret.db_password_secret,
    google_service_account.gce_sa
  ]
}

# Grant GCE SA permission to connect to Cloud SQL
resource "google_project_iam_member" "gce_sa_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.gce_sa.email}"
  depends_on = [
    google_sql_database_instance.main,
    google_service_account.gce_sa
  ]
}

# GCE Instance to run OpenFGA
resource "google_compute_instance" "openfga_vm" {
  project      = var.project_id
  zone         = var.zone
  name         = var.gce_instance_name
  machine_type = var.gce_machine_type
  tags         = ["openfga-server", "allow-http", "allow-grpc", "allow-playground"]

  boot_disk {
    initialize_params {
      image = var.gce_boot_image
    }
  }

  network_interface {
    network = "default" # Use default VPC network
    access_config {
      // Ephemeral public IP will be assigned
    }
  }

  service_account {
    email  = google_service_account.gce_sa.email
    scopes = ["cloud-platform"] # Allows the SA to use its granted IAM roles
  }

  metadata = {
    # Information passed to the startup script
    db_user                       = google_sql_user.openfga_user.name
    db_name                       = google_sql_database.openfga_db.name
    db_instance_connection_name   = google_sql_database_instance.main.connection_name
    db_password_secret_name       = google_secret_manager_secret.db_password_secret.secret_id # Short name
    db_password_secret_project_id = google_secret_manager_secret.db_password_secret.project
    db_password_secret_version    = google_secret_manager_secret_version.db_password_secret_version.version # Specific version
    openfga_image_name            = var.openfga_image
    openfga_playground_setting    = var.enable_openfga_playground ? "true" : "false"
    openfga_log_level             = "info" # or "debug"
  }

  metadata_startup_script = file("./startup_script.sh")

  allow_stopping_for_update = true # Useful for updating instance template without recreation

  depends_on = [
    google_project_service.compute_api,
    google_sql_database_instance.main,
    google_sql_user.openfga_user,
    google_secret_manager_secret_version.db_password_secret_version,
    google_service_account.gce_sa,
    google_project_iam_member.gce_sa_sql_client,
    google_secret_manager_secret_iam_member.gce_sa_db_password_accessor
  ]
}

# Firewall Rules
resource "google_compute_firewall" "allow_ssh" {
  project = var.project_id
  name    = "openfga-allow-ssh"
  network = "default" # Or your custom VPC network
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"]      # WARNING: For production, restrict to known IPs
  target_tags   = ["openfga-server"] # Applied to the GCE instance
}

resource "google_compute_firewall" "allow_openfga_http" {
  project = var.project_id
  name    = "openfga-allow-http-8080"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["8080"] # OpenFGA HTTP API
  }
  source_ranges = ["0.0.0.0/0"] # Allow from anywhere
  target_tags   = ["allow-http", "openfga-server"]
}

resource "google_compute_firewall" "allow_openfga_grpc" {
  project = var.project_id
  name    = "openfga-allow-grpc-8081"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["8081"] # OpenFGA gRPC API
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-grpc", "openfga-server"]
}

resource "google_compute_firewall" "allow_openfga_playground" {
  project = var.project_id
  name    = "openfga-allow-playground-3000"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["3000"] # OpenFGA Playground
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-playground", "openfga-server"]
  # Only create this firewall rule if playground is enabled
  count = var.enable_openfga_playground ? 1 : 0
}
