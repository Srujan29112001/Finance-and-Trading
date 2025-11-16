# Variables for AWS Terraform Deployment

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "finance-analytics"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "financeuser"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "kafka_broker_count" {
  description = "Number of Kafka brokers"
  type        = number
  default     = 3
}

variable "kafka_instance_type" {
  description = "Kafka broker instance type"
  type        = string
  default     = "kafka.m5.xlarge"
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "neptune_instance_class" {
  description = "Neptune instance class"
  type        = string
  default     = "db.r5.large"
}

variable "emr_master_instance_type" {
  description = "EMR master instance type"
  type        = string
  default     = "m5.xlarge"
}

variable "emr_core_instance_type" {
  description = "EMR core instance type"
  type        = string
  default     = "m5.2xlarge"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Finance Analytics"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}
