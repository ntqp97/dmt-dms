import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
import io


class S3FileManager:
    @staticmethod
    def s3_connection(aws_access_key_id, aws_secret_access_key, region_name):
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
            return s3
        except ClientError as e:
            return None

    @staticmethod
    def create_s3_bucket(bucket_name: str, s3_client, region: str = 'us-east-1'):
        try:
            if region is None:
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                location = {'LocationConstraint': region}
                s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
            return True
        except ClientError as e:
            print(e)
            return False

    @staticmethod
    def upload_file_to_s3(local_file_path: str, bucket_name: str, s3_object_name: str, s3_client):
        try:
            # Upload the file
            s3_client.upload_file(local_file_path, bucket_name, s3_object_name)
            print(f"File uploaded successfully to {bucket_name}/{s3_object_name}")
            return True
        except NoCredentialsError:
            print("Credentials not available")
            return False

    @staticmethod
    def check_file_exists_in_s3(bucket_name, s3_file_key, s3_client):
        try:
            # Head object to check if the file exists
            s3_client.head_object(Bucket=bucket_name, Key=s3_file_key)
            print(f"File '{s3_file_key}' exists in bucket '{bucket_name}'")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"File '{s3_file_key}' does not exist in bucket '{bucket_name}'")
                return False
            else:
                print(f"Error checking file existence: {e}")
                return False
        except (NoCredentialsError, PartialCredentialsError):
            print("Credentials not available")
            return False

    @staticmethod
    def delete_file_from_s3(bucket_name, file_key, s3_client):
        # AWS credentials (replace with your own)
        try:
            # Delete the file
            s3_client.delete_object(Bucket=bucket_name, Key=file_key)
            print(f"File '{file_key}' deleted successfully from bucket '{bucket_name}'")
            return True
        except NoCredentialsError:
            print("Credentials not available")
            return False

    @staticmethod
    def create_presigned_url(s3_client, bucket_name, object_name, expiration=3600):
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            print(e)
            return None

    @staticmethod
    def download_file_from_s3(bucket_name, file_key, local_path, s3_client):
        try:
            # Download the file from S3
            s3_client.download_file(bucket_name, file_key, local_path)
            print(f"File downloaded successfully: {local_path}")
            return True
        except NoCredentialsError:
            print("Credentials not available")
            return False

    @staticmethod
    def get_pdf_from_s3(bucket_name, file_key, s3_client):
        input_pdf = io.BytesIO()
        try:
            s3_client.download_fileobj(bucket_name, file_key, input_pdf)
            input_pdf.seek(0)
            return input_pdf
        except Exception as e:
            raise Exception(f"Error downloading file from S3: {str(e)}")
