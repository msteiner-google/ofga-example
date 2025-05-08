variable "project_id" {
  description = "The Google Cloud project ID."
  type        = string
  default     = "msteiner-joonix"
}

variable "region" {
  description = "The Google Cloud region for resources."
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "The Google Cloud zone for the GCE instance (e.g., us-central1-a)."
  type        = string
  default     = "europe-west1-d" # Or provide it explicitly
}

variable "cloud_sql_instance_name" {
  description = "Name for the Cloud SQL instance."
  type        = string
  default     = "openfga-postgres-db"
}

variable "cloud_sql_tier" {
  description = "The machine type for the Cloud SQL instance."
  type        = string
  default     = "db-g1-small"
}

variable "cloud_sql_db_name" {
  description = "Name of the database inside the Cloud SQL instance for OpenFGA."
  type        = string
  default     = "openfgadb"
}

variable "cloud_sql_user_name" {
  description = "Username for OpenFGA to connect to the database."
  type        = string
  default     = "openfgauser"
}

variable "gce_instance_name" {
  description = "Name for the GCE instance running OpenFGA."
  type        = string
  default     = "openfga-server-vm"
}

variable "gce_machine_type" {
  description = "Machine type for the GCE instance."
  type        = string
  default     = "e2-medium" # Provides a good balance for a small server
}

variable "gce_boot_image" {
  description = "Boot image for the GCE instance."
  type        = string
  default     = "debian-cloud/debian-11"
}

variable "openfga_image" {
  description = "The Docker image for OpenFGA server."
  type        = string
  default     = "openfga/openfga:v1.8"
}

variable "enable_openfga_playground" {
  description = "Enable the OpenFGA playground UI."
  type        = bool
  default     = true
}
