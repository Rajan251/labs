#!/bin/bash
# Script to create Terraform backend resources (S3 + DynamoDB)

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-default}"
BUCKET_NAME="terraform-state-$(aws sts get-caller-identity --query Account --output text --profile ${AWS_PROFILE})"
DYNAMODB_TABLE="terraform-state-lock"

echo "Creating Terraform backend resources..."
echo "Region: ${AWS_REGION}"
echo "Profile: ${AWS_PROFILE}"
echo "Bucket: ${BUCKET_NAME}"
echo "DynamoDB Table: ${DYNAMODB_TABLE}"
echo ""

# Create S3 bucket
echo "Creating S3 bucket..."
if aws s3api head-bucket --bucket "${BUCKET_NAME}" --profile ${AWS_PROFILE} 2>/dev/null; then
    echo "Bucket ${BUCKET_NAME} already exists"
else
    aws s3api create-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${AWS_REGION}" \
        --profile ${AWS_PROFILE}
    echo "✓ Bucket created"
fi

# Enable versioning
echo "Enabling versioning..."
aws s3api put-bucket-versioning \
    --bucket "${BUCKET_NAME}" \
    --versioning-configuration Status=Enabled \
    --profile ${AWS_PROFILE}
echo "✓ Versioning enabled"

# Enable encryption
echo "Enabling encryption..."
aws s3api put-bucket-encryption \
    --bucket "${BUCKET_NAME}" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }' \
    --profile ${AWS_PROFILE}
echo "✓ Encryption enabled"

# Block public access
echo "Blocking public access..."
aws s3api put-public-access-block \
    --bucket "${BUCKET_NAME}" \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --profile ${AWS_PROFILE}
echo "✓ Public access blocked"

# Create DynamoDB table
echo "Creating DynamoDB table..."
if aws dynamodb describe-table --table-name "${DYNAMODB_TABLE}" --profile ${AWS_PROFILE} 2>/dev/null; then
    echo "Table ${DYNAMODB_TABLE} already exists"
else
    aws dynamodb create-table \
        --table-name "${DYNAMODB_TABLE}" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "${AWS_REGION}" \
        --profile ${AWS_PROFILE}
    
    echo "Waiting for table to be active..."
    aws dynamodb wait table-exists \
        --table-name "${DYNAMODB_TABLE}" \
        --profile ${AWS_PROFILE}
    echo "✓ Table created"
fi

echo ""
echo "Backend resources created successfully!"
echo ""
echo "Add this to your backend.tf:"
echo ""
echo "terraform {"
echo "  backend \"s3\" {"
echo "    bucket         = \"${BUCKET_NAME}\""
echo "    key            = \"envs/ENV_NAME/terraform.tfstate\""
echo "    region         = \"${AWS_REGION}\""
echo "    encrypt        = true"
echo "    dynamodb_table = \"${DYNAMODB_TABLE}\""
echo "    profile        = \"${AWS_PROFILE}\""
echo "  }"
echo "}"
