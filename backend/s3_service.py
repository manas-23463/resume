import boto3
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class S3Service:
    def __init__(self):
        """Initialize S3 service with AWS credentials"""
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'lisa-research')
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
        
        print(f"S3 Service initialized with bucket: {self.bucket_name}")
    
    def upload_resume(self, file_path: str, user_id: str, original_filename: str) -> Optional[str]:
        """Upload a resume file to S3 and return the S3 URL"""
        try:
            # Generate unique S3 key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'pdf'
            s3_key = f"resumes/{user_id}/{timestamp}_{original_filename}"
            
            # Upload file to S3
            with open(file_path, 'rb') as file:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': self._get_content_type(file_extension),
                        'Metadata': {
                            'user_id': user_id,
                            'original_filename': original_filename,
                            'upload_timestamp': timestamp
                        }
                    }
                )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            print(f"Resume uploaded to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"Error uploading resume to S3: {e}")
            return None
    
    def upload_resume_from_bytes(self, file_content: bytes, user_id: str, original_filename: str) -> Optional[str]:
        """Upload resume from bytes to S3 and return the S3 URL"""
        try:
            # Generate unique S3 key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'pdf'
            s3_key = f"resumes/{user_id}/{timestamp}_{original_filename}"
            
            # Upload file to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(file_extension),
                Metadata={
                    'user_id': user_id,
                    'original_filename': original_filename,
                    'upload_timestamp': timestamp
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            print(f"Resume uploaded to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            print(f"Error uploading resume to S3: {e}")
            return None
    
    def delete_resume(self, s3_url: str) -> bool:
        """Delete a resume from S3 using the S3 URL"""
        try:
            # Extract S3 key from URL
            s3_key = s3_url.split(f"{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/")[-1]
            
            # Delete object from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            print(f"Resume deleted from S3: {s3_url}")
            return True
            
        except Exception as e:
            print(f"Error deleting resume from S3: {e}")
            return False
    
    def _get_content_type(self, file_extension: str) -> str:
        """Get appropriate content type for file extension"""
        content_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def test_connection(self) -> bool:
        """Test S3 connection and bucket access"""
        try:
            # Try to list objects in the bucket
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            print(f"S3 connection successful. Bucket: {self.bucket_name}")
            return True
        except Exception as e:
            print(f"S3 connection failed: {e}")
            return False

# Initialize S3 service
s3_service = S3Service()
