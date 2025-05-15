# Enable necessary APIs
resource "google_project_service" "run_api" {
  project            = var.project_id
  service            = "run.googleapis.com"
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

data "google_compute_default_service_account" "default" {
  project = var.project_id
}

# Store the database password in Secret Manager
resource "google_secret_manager_secret" "db_password_secret" {
  project   = var.project_id
  secret_id = "${var.cloud_sql_instance_name}-db-password"

  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager_api]
}

resource "google_secret_manager_secret_version" "db_password_secret_version" {
  secret      = google_secret_manager_secret.db_password_secret.id
  secret_data = random_password.db_password.result
}

data "google_iam_policy" "admin" {
  binding {
    role = "roles/secretmanager.secretAccessor"
    members = [
      "serviceAccount:${data.google_compute_default_service_account.default.email}",
    ]
  }
}

resource "google_secret_manager_secret_iam_policy" "policy" {
  project     = var.project_id
  secret_id   = google_secret_manager_secret.db_password_secret.id
  policy_data = data.google_iam_policy.admin.policy_data
}

# Cloud SQL Postgres Instance
resource "google_sql_database_instance" "main" {
  project             = var.project_id
  name                = var.cloud_sql_instance_name
  region              = var.region
  database_version    = "POSTGRES_14"
  deletion_protection = false # Set to true for production

  settings {
    tier = var.cloud_sql_tier
    ip_configuration {
      ipv4_enabled = true # Not strictly needed for Cloud Run direct connection
    }
    # Ensure backups are enabled for production
    # backup_configuration {
    #   enabled = true
    # }
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


resource "google_cloud_run_v2_job" "openfga_run_migrations" {
  project             = var.project_id
  name                = "run_db_migrations"
  location            = var.region
  deletion_protection = false # Set to true for production if desired
  template {
    template {


      service_account       = data.google_compute_default_service_account.default.email
      execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

      # Volume for Cloud SQL socket
      volumes {
        name = "cloudsql" # An arbitrary name for the volume
        cloud_sql_instance {
          instances = [google_sql_database_instance.main.connection_name]
        }
      }

      containers {
        image = var.openfga_image

        env {
          name  = "OPENFGA_DATASTORE_ENGINE"
          value = "postgres"
        }
        env {
          name = "OPENFGA_DATASTORE_URI"
          # The Cloud SQL socket will be at /cloudsql/INSTANCE_CONNECTION_NAME
          # Adding sslmode=disable is often necessary for Unix socket connections to PostgreSQL.
          value = "postgres:///postgres?host=/cloudsql/${google_sql_database_instance.main.connection_name}&sslmode=disable"
        }
        env {
          name  = "OPENFGA_DATASTORE_USERNAME"
          value = google_sql_user.openfga_user.name
        }
        env {
          name = "OPENFGA_DATASTORE_PASSWORD" # This variable will be substituted in OPENFGA_DATASTORE_URI
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.db_password_secret.secret_id # Short name of the secret
              version = "latest"                                                  # Or specific version: google_secret_manager_secret_version.db_password_secret_version.version
            }
          }
        }
        env {
          name  = "OPENFGA_HTTP_ADDR"
          value = ":8080"
        }
        env {
          name  = "OPENFGA_GRPC_ADDR"
          value = ":8081"
        }
        env {
          name  = "OPENFGA_PLAYGROUND_ENABLED"
          value = var.enable_openfga_playground ? "true" : "false"
        }
        env {
          name  = "OPENFGA_LOG_FORMAT" # Recommended for Cloud Logging
          value = "json"
        }
        env {
          name  = "OPENFGA_AUTHN_METHOD" # For no auth. Use "preshared" for preshared key auth.
          value = "none"
        }

        # Mount the Cloud SQL volume
        volume_mounts {
          name       = "cloudsql"  # Must match the volume name defined above
          mount_path = "/cloudsql" # Standard directory where sockets are placed
        }
        args = ["migrate"]
      }
    }
  }
  provisioner "local-exec" {
    when    = create # IMPORTANT: Only run on creation
    command = <<-EOT
      gcloud beta run jobs execute ${self.name} \
        --region ${self.location} \
        --project ${self.project} \
        --wait
    EOT
    # Optional: Set environment variables for the gcloud command if needed
    # environment = {
    #   CLOUDSDK_CORE_PROJECT = self.project
    # }
    # Optional: Specify interpreter if not bash/sh
    # interpreter = ["bash", "-c"]
  }
}

# Cloud Run Service for OpenFGA
resource "google_cloud_run_v2_service" "openfga_service" {
  project             = var.project_id
  name                = var.cloud_run_service_name
  location            = var.region
  deletion_protection = false                 # Set to true for production if desired
  ingress             = "INGRESS_TRAFFIC_ALL" # Allows all traffic, including from the internet

  template {
    service_account       = data.google_compute_default_service_account.default.email
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2" # Or GEN1 if preferred/needed

    # Optional: Scaling configuration
    scaling {
      min_instance_count = 0 # Set to 1 for no cold starts on first request (but incurs cost)
      max_instance_count = 5 # Adjust as needed
    }

    # Volume for Cloud SQL socket
    volumes {
      name = "cloudsql" # An arbitrary name for the volume
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }

    containers {
      image = var.openfga_image
      ports {
        container_port = 8080 # OpenFGA default HTTP port. Adjust if your image uses a different one.
        # Cloud Run will map its external port to this container port.
      }

      # Environment variables - each as a separate block
      env {
        name  = "OPENFGA_DATASTORE_ENGINE"
        value = "postgres"
      }
      env {
        name = "OPENFGA_DATASTORE_URI"
        # The Cloud SQL socket will be at /cloudsql/INSTANCE_CONNECTION_NAME
        # Adding sslmode=disable is often necessary for Unix socket connections to PostgreSQL.
        value = "postgres:///postgres?host=/cloudsql/${google_sql_database_instance.main.connection_name}&sslmode=disable"
      }
      env {
        name  = "OPENFGA_DATASTORE_USERNAME"
        value = google_sql_user.openfga_user.name
      }
      env {
        name = "OPENFGA_DATASTORE_PASSWORD" # This variable will be substituted in OPENFGA_DATASTORE_URI
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_password_secret.secret_id # Short name of the secret
            version = "latest"                                                  # Or specific version: google_secret_manager_secret_version.db_password_secret_version.version
          }
        }
      }
      env {
        name  = "OPENFGA_HTTP_ADDR"
        value = ":8080"
      }
      env {
        name  = "OPENFGA_GRPC_ADDR"
        value = ":8081"
      }
      env {
        name  = "OPENFGA_PLAYGROUND_ENABLED"
        value = var.enable_openfga_playground ? "true" : "false"
      }
      env {
        name  = "OPENFGA_LOG_FORMAT" # Recommended for Cloud Logging
        value = "json"
      }
      env {
        name  = "OPENFGA_AUTHN_METHOD" # For no auth. Use "preshared" for preshared key auth.
        value = "none"
      }
      # If your OpenFGA image expects the $PORT environment variable from Cloud Run,
      # you can set OPENFGA_HTTP_ADDR to ":$PORT" or ensure OpenFGA reads $PORT.
      # However, OpenFGA typically uses its own config flags/env vars like OPENFGA_HTTP_ADDR.
      # env {
      #   name = "PORT"
      #   value = "8080" # This is informational if OpenFGA doesn't directly use $PORT
      # }

      # Mount the Cloud SQL volume
      volume_mounts {
        name       = "cloudsql"  # Must match the volume name defined above
        mount_path = "/cloudsql" # Standard directory where sockets are placed
      }

      # Optional: Configure probes for health checking
      startup_probe {
        initial_delay_seconds = 10 # Give OpenFGA time to start and run migrations
        period_seconds        = 10
        timeout_seconds       = 5
        failure_threshold     = 3
        http_get {
          path = "/healthz" # OpenFGA health check endpoint
          port = 8080       # Port inside the container
        }
      }
      liveness_probe {
        period_seconds    = 15
        timeout_seconds   = 5
        failure_threshold = 3
        http_get {
          path = "/healthz"
          port = 8080
        }
      }
      # command = ["printenv"]
      args = ["run"]

      # Optional: Define resource requests and limits
      # resources {
      #   limits = {
      #     cpu    = "1000m" # 1 vCPU
      #     memory = "512Mi"
      #   }
      #   # requests = {
      #   #   cpu    = "250m"
      #   #   memory = "256Mi"
      #   # }
      # }
    }
  }

  # Automatically route 100% traffic to the latest revision
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.run_api,
    google_sql_database_instance.main,
    google_sql_user.openfga_user,
    google_secret_manager_secret_version.db_password_secret_version,
    google_cloud_run_v2_job.openfga_run_migrations,
  ]
}

# Output the URL of the Cloud Run service
output "openfga_service_url" {
  description = "URL of the deployed OpenFGA Cloud Run service."
  value       = google_cloud_run_v2_service.openfga_service.uri
}
