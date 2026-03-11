import boto3
import os
from flask import current_app
from botocore.exceptions import ClientError
import tempfile
import urllib.parse

class S3Service:
    def __init__(self):
        self._s3_client = None

    @property
    def client(self):
        if self._s3_client is None:
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=current_app.config.get('AWS_DEFAULT_REGION')
            )
        return self._s3_client

    def parse_s3_url(self, s3_url):
        """Parse s3://bucket/key URL into bucket and key."""
        parsed = urllib.parse.urlparse(s3_url)
        if parsed.scheme != 's3':
            raise ValueError(f"Invalid S3 URL format: {s3_url}")
        bucket = parsed.netloc
        key = parsed.path.lstrip('/')
        return bucket, key

    def download_file(self, s3_url):
        """
        Downloads a file from S3 to a temporary local file.
        Returns the path to the temporary file.
        """
        bucket, key = self.parse_s3_url(s3_url)
        
        # Get original extension
        _, ext = os.path.splitext(key)
        
        try:
            # Create a temporary file with the same extension
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd) # Close file descriptor, boto3 will open it
            
            current_app.logger.info(f"Downloading s3://{bucket}/{key} to {temp_path}")
            self.client.download_file(bucket, key, temp_path)
            
            return temp_path
        except ClientError as e:
            current_app.logger.error(f"Error downloading from S3: {e}")
            # Clean up temp file if download failed but file was created
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

s3_service = S3Service()
