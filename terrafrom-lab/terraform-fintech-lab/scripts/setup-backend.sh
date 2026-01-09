#!/bin/bash
# Setup script for Terraform backend (S3 + DynamoDB)

set -e

BUCKET_NAME="payflow-terraform-state"
DYNAMODB_TABLE="payflow-terraform-locks"
AWS_REGION="us-east-1"

echo "Setting up Terraform backend infrastructure..."

# Create S3 bucket for state
echo "Creating S3 bucket: $BUCKET_NAME"
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $AWS_REGION \
  2>/dev/null || echo "Bucket already exists"

# Enable versioning
echo "Enabling versioning on S3 bucket"
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Enable encryption
echo "Enabling encryption on S3 bucket"
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
echo "Blocking public access to S3 bucket"
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create DynamoDB table for state locking
echo "Creating DynamoDB table: $DYNAMODB_TABLE"
aws dynamodb create-table \
  --table-name $DYNAMODB_TABLE \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $AWS_REGION \
  2>/dev/null || echo "Table already exists"

echo ""
echo "✅ Terraform backend setup complete!"
echo ""
echo "Backend Configuration:"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  DynamoDB Table: $DYNAMODB_TABLE"
echo "  Region: $AWS_REGION"
echo ""
echo "Add this to your Terraform configuration:"
echo ""
echo "terraform {"
echo "  backend \"s3\" {"
echo "    bucket         = \"$BUCKET_NAME\""
echo "    key            = \"<environment>/terraform.tfstate\""
echo "    region         = \"$AWS_REGION\""
echo "    encrypt        = true"
echo "    dynamodb_table = \"$DYNAMODB_TABLE\""
echo "  }"
echo "}"
