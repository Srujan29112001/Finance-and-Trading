# Terraform Configuration for Finance Analytics Platform on AWS
# Deploys: EKS cluster, RDS, MSK (Kafka), ElastiCache (Redis),
# Neptune (Graph DB), S3 (Data Lake), EMR (Spark)

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "finance-analytics-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "dev" ? true : false
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-vpc"
    }
  )
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.project_name}-eks"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster access configuration
  cluster_endpoint_public_access = true

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 10

      instance_types = ["t3.xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "general"
      }

      tags = merge(
        var.common_tags,
        {
          Name = "${var.project_name}-general-nodes"
        }
      )
    }

    ml_workloads = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["g4dn.xlarge"]  # GPU instances for ML
      capacity_type  = "SPOT"

      labels = {
        role = "ml"
      }

      taints = [{
        key    = "ml-workload"
        value  = "true"
        effect = "NoSchedule"
      }]

      tags = merge(
        var.common_tags,
        {
          Name = "${var.project_name}-ml-nodes"
        }
      )
    }
  }

  tags = var.common_tags
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project_name}-postgres-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-postgres-subnet"
    }
  )
}

resource "aws_db_instance" "postgres" {
  identifier     = "${var.project_name}-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.rds_instance_class

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true

  db_name  = "financedb"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  multi_az               = var.environment == "prod" ? true : false
  skip_final_snapshot    = var.environment == "dev" ? true : false
  final_snapshot_identifier = "${var.project_name}-postgres-final"

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-postgres"
    }
  )
}

# MSK (Managed Kafka)
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "${var.project_name}-msk"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = var.kafka_broker_count

  broker_node_group_info {
    instance_type  = var.kafka_instance_type
    client_subnets = module.vpc.private_subnets

    storage_info {
      ebs_storage_info {
        volume_size = 1000
      }
    }

    security_groups = [aws_security_group.msk.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }

  tags = var.common_tags
}

# ElastiCache (Redis)
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = var.common_tags
}

# Neptune (Graph Database)
resource "aws_neptune_subnet_group" "neptune" {
  name       = "${var.project_name}-neptune-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-neptune-subnet"
    }
  )
}

resource "aws_neptune_cluster" "neptune" {
  cluster_identifier  = "${var.project_name}-neptune"
  engine              = "neptune"
  skip_final_snapshot = var.environment == "dev" ? true : false

  vpc_security_group_ids          = [aws_security_group.neptune.id]
  neptune_subnet_group_name       = aws_neptune_subnet_group.neptune.name
  backup_retention_period         = 7
  preferred_backup_window         = "03:00-04:00"
  preferred_maintenance_window    = "sun:04:00-sun:05:00"

  tags = var.common_tags
}

resource "aws_neptune_cluster_instance" "neptune" {
  count              = 2
  identifier         = "${var.project_name}-neptune-${count.index}"
  cluster_identifier = aws_neptune_cluster.neptune.id
  instance_class     = var.neptune_instance_class

  tags = var.common_tags
}

# S3 Data Lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-data-lake"

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-data-lake"
    }
  )
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# EMR for Spark
resource "aws_emr_cluster" "spark" {
  name          = "${var.project_name}-spark-emr"
  release_label = "emr-6.14.0"
  applications  = ["Spark", "Hadoop", "Hive"]

  service_role = aws_iam_role.emr_service_role.arn

  ec2_attributes {
    instance_profile                  = aws_iam_instance_profile.emr_profile.arn
    emr_managed_master_security_group = aws_security_group.emr_master.id
    emr_managed_slave_security_group  = aws_security_group.emr_slave.id
    subnet_id                         = module.vpc.private_subnets[0]
  }

  master_instance_group {
    instance_type  = var.emr_master_instance_type
    instance_count = 1
  }

  core_instance_group {
    instance_type  = var.emr_core_instance_type
    instance_count = 3

    ebs_config {
      size                 = 500
      type                 = "gp3"
      volumes_per_instance = 1
    }
  }

  configurations_json = <<EOF
[
  {
    "Classification": "spark-defaults",
    "Properties": {
      "spark.sql.warehouse.dir": "s3://${aws_s3_bucket.data_lake.bucket}/warehouse/",
      "spark.eventLog.enabled": "true",
      "spark.eventLog.dir": "s3://${aws_s3_bucket.data_lake.bucket}/spark-logs/"
    }
  }
]
EOF

  tags = var.common_tags
}

# Security Groups
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.common_tags
}

resource "aws_security_group" "msk" {
  name        = "${var.project_name}-msk-sg"
  description = "Security group for MSK"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.common_tags
}

resource "aws_security_group" "redis" {
  name        = "${var.project_name}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  tags = var.common_tags
}

resource "aws_security_group" "neptune" {
  name        = "${var.project_name}-neptune-sg"
  description = "Security group for Neptune"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 8182
    to_port     = 8182
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }

  tags = var.common_tags
}

resource "aws_security_group" "emr_master" {
  name        = "${var.project_name}-emr-master-sg"
  description = "Security group for EMR master nodes"
  vpc_id      = module.vpc.vpc_id

  tags = var.common_tags
}

resource "aws_security_group" "emr_slave" {
  name        = "${var.project_name}-emr-slave-sg"
  description = "Security group for EMR slave nodes"
  vpc_id      = module.vpc.vpc_id

  tags = var.common_tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "msk" {
  name              = "/aws/msk/${var.project_name}"
  retention_in_days = 7

  tags = var.common_tags
}

# IAM Roles for EMR
resource "aws_iam_role" "emr_service_role" {
  name = "${var.project_name}-emr-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "elasticmapreduce.amazonaws.com"
      }
    }]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "emr_service_policy" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

resource "aws_iam_role" "emr_instance_profile_role" {
  name = "${var.project_name}-emr-instance-profile-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = var.common_tags
}

resource "aws_iam_instance_profile" "emr_profile" {
  name = "${var.project_name}-emr-profile"
  role = aws_iam_role.emr_instance_profile_role.name
}

resource "aws_iam_role_policy_attachment" "emr_instance_policy" {
  role       = aws_iam_role.emr_instance_profile_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

# Outputs
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "msk_bootstrap_brokers" {
  description = "MSK Kafka bootstrap brokers"
  value       = aws_msk_cluster.kafka.bootstrap_brokers_tls
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "neptune_endpoint" {
  description = "Neptune cluster endpoint"
  value       = aws_neptune_cluster.neptune.endpoint
}

output "data_lake_bucket" {
  description = "S3 data lake bucket name"
  value       = aws_s3_bucket.data_lake.bucket
}

output "emr_master_public_dns" {
  description = "EMR master node DNS"
  value       = aws_emr_cluster.spark.master_public_dns
}
