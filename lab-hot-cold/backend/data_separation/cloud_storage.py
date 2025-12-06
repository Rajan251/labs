"""
Cloud Storage Adapter for Cold Data (S3/MinIO/GCS)

This module provides adapters for storing cold data in cloud object storage
while keeping hot data in MongoDB.

Supported backends:
- AWS S3
- MinIO (S3-compatible)
- Google Cloud Storage (GCS)
- Azure Blob Storage
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import cloud storage libraries
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("boto3 not installed. S3 support disabled.")

try:
    from google.cloud import storage as gcs_storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not installed. GCS support disabled.")

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("azure-storage-blob not installed. Azure support disabled.")


class CloudStorageAdapter:
    """Base adapter for cloud storage"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.backend = config.get('backend', 's3')
        
    async def upload(self, key: str, data: Dict) -> bool:
        """Upload data to cloud storage"""
        raise NotImplementedError
    
    async def download(self, key: str) -> Optional[Dict]:
        """Download data from cloud storage"""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Delete data from cloud storage"""
        raise NotImplementedError
    
    async def list_keys(self, prefix: str) -> List[str]:
        """List keys with given prefix"""
        raise NotImplementedError


class S3Adapter(CloudStorageAdapter):
    """AWS S3 / MinIO adapter"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        if not S3_AVAILABLE:
            raise ImportError("boto3 is required for S3. Install: pip install boto3")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=config.get('endpoint'),  # For MinIO
            aws_access_key_id=config.get('access_key'),
            aws_secret_access_key=config.get('secret_key'),
            region_name=config.get('region', 'us-east-1')
        )
        
        self.bucket = config.get('bucket')
        logger.info(f"✓ S3 adapter initialized for bucket: {self.bucket}")
    
    async def upload(self, key: str, data: Dict) -> bool:
        """Upload JSON data to S3"""
        try:
            # Convert data to JSON
            json_data = json.dumps(data, default=str)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'source': 'hot_cold_migration'
                }
            )
            
            logger.info(f"✓ Uploaded to S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"✗ S3 upload failed: {e}")
            return False
    
    async def download(self, key: str) -> Optional[Dict]:
        """Download JSON data from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=key
            )
            
            # Parse JSON
            json_data = response['Body'].read().decode('utf-8')
            data = json.loads(json_data)
            
            logger.info(f"✓ Downloaded from S3: {key}")
            return data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Key not found in S3: {key}")
                return None
            logger.error(f"✗ S3 download failed: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete object from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            logger.info(f"✓ Deleted from S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"✗ S3 delete failed: {e}")
            return False
    
    async def list_keys(self, prefix: str) -> List[str]:
        """List all keys with given prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            keys = [obj['Key'] for obj in response['Contents']]
            return keys
            
        except ClientError as e:
            logger.error(f"✗ S3 list failed: {e}")
            return []


class MinIOAdapter(S3Adapter):
    """MinIO adapter (uses S3 adapter with custom endpoint)"""
    
    def __init__(self, config: Dict):
        # MinIO is S3-compatible, just use S3 adapter
        super().__init__(config)
        logger.info(f"✓ MinIO adapter initialized")


class GCSAdapter(CloudStorageAdapter):
    """Google Cloud Storage adapter"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        if not GCS_AVAILABLE:
            raise ImportError("google-cloud-storage is required. Install: pip install google-cloud-storage")
        
        # Initialize GCS client
        self.client = gcs_storage.Client()
        self.bucket = self.client.bucket(config.get('bucket'))
        logger.info(f"✓ GCS adapter initialized for bucket: {config.get('bucket')}")
    
    async def upload(self, key: str, data: Dict) -> bool:
        """Upload JSON data to GCS"""
        try:
            blob = self.bucket.blob(key)
            json_data = json.dumps(data, default=str)
            
            blob.upload_from_string(
                json_data,
                content_type='application/json'
            )
            
            logger.info(f"✓ Uploaded to GCS: {key}")
            return True
            
        except Exception as e:
            logger.error(f"✗ GCS upload failed: {e}")
            return False
    
    async def download(self, key: str) -> Optional[Dict]:
        """Download JSON data from GCS"""
        try:
            blob = self.bucket.blob(key)
            
            if not blob.exists():
                logger.warning(f"Key not found in GCS: {key}")
                return None
            
            json_data = blob.download_as_text()
            data = json.loads(json_data)
            
            logger.info(f"✓ Downloaded from GCS: {key}")
            return data
            
        except Exception as e:
            logger.error(f"✗ GCS download failed: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete blob from GCS"""
        try:
            blob = self.bucket.blob(key)
            blob.delete()
            
            logger.info(f"✓ Deleted from GCS: {key}")
            return True
            
        except Exception as e:
            logger.error(f"✗ GCS delete failed: {e}")
            return False
    
    async def list_keys(self, prefix: str) -> List[str]:
        """List all blobs with given prefix"""
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            keys = [blob.name for blob in blobs]
            return keys
            
        except Exception as e:
            logger.error(f"✗ GCS list failed: {e}")
            return []


def get_cloud_adapter(config: Dict) -> CloudStorageAdapter:
    """Factory function to get appropriate cloud adapter"""
    
    backend = config.get('backend', 's3').lower()
    
    if backend == 's3':
        return S3Adapter(config)
    elif backend == 'minio':
        return MinIOAdapter(config)
    elif backend == 'gcs':
        return GCSAdapter(config)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def build_storage_key(collection: str, document_id: str) -> str:
    """Build storage key for cloud object"""
    # Format: collection/year/month/document_id.json
    now = datetime.utcnow()
    return f"{collection}/{now.year}/{now.month:02d}/{document_id}.json"
