variable "project_id" {
  description = "The Google Cloud project ID."
  type        = string
  default     = "msteiner-kubeflow"
}

variable "region" {
  description = "The Google Cloud region for resources."
  type        = string
  default     = "europe-west4"
}
variable "cloud_sql_instance_name" {
  description = "Name for the Cloud SQL instance."
  type        = string
  default     = "openfga-db-instance"
}

variable "cloud_sql_tier" {
  description = "Machine type for Cloud SQL (e.g., db-f1-micro, db-g1-small)."
  type        = string
  default     = "db-g1-small" # Choose based on needs
}

variable "cloud_sql_db_name" {
  description = "Name for the OpenFGA database."
  type        = string
  default     = "openfgadb"
}

variable "cloud_sql_user_name" {
  description = "Username for OpenFGA to connect to the database."
  type        = string
  default     = "openfgauser"
}

variable "openfga_image" {
  description = "The OpenFGA Docker image to deploy (e.g., openfga/openfga:latest)."
  type        = string
  default     = "openfga/openfga:v1.8.11"
}

variable "enable_openfga_playground" {
  description = "Enable the OpenFGA Playground UI."
  type        = bool
  default     = true
}

variable "cloud_run_service_name" {
  description = "Name for the Cloud Run service."
  type        = string
  default     = "openfga-server"
}
