from dotenv import load_dotenv
import os
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Charger le .env (priorité aux variables d'environnement système)
# On ne charge le .env que si on n'est pas déjà dans un environnement configuré (ex: local dev)
if not os.getenv('AWS_ACCESS_KEY_ID'):
    BASE_DIR = Path(__file__).resolve().parent
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    load_dotenv() # Fallback to CWD .env

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('region', os.getenv('AWS_REGION', 'eu-north-1'))
bucket_name = os.getenv('bucket_name', os.getenv('AWS_STORAGE_BUCKET_NAME', 'noxapdfbucket'))

# Debug (safe version)
if os.getenv('DEBUG', 'False') == 'True':
    print("=" * 60)
    print("[DEBUG] AWS Service Configuration")
    print(f"[KEY] AWS_ACCESS_KEY_ID: {'FOUND' if AWS_ACCESS_KEY_ID else 'NOT FOUND'}")
    print(f"[KEY] AWS_SECRET_ACCESS_KEY: {'FOUND' if AWS_SECRET_ACCESS_KEY else 'NOT FOUND'}")
    print(f"[BUCKET] Bucket name: {bucket_name}")
    print(f"[REGION] Region: {region}")
    print("=" * 60)


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=region
)

# send a file to s3 bucket and get the download url

def get_signed_url(object_name, expiration=3600):
    """Generate a presigned URL for private S3 objects"""
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL: {e}")
        return None



def upload_file_to_s3(file, s3_path, public=True):
    """
    Upload a file to AWS S3 and return the file URL.
    
    :param file: Django UploadedFile object to upload
    :param s3_path: Destination path in S3 (example: 'subjects/2025/math.pdf')
    :param public: If True, file will be public, otherwise private
    """

    # Validate bucket_name
    if not bucket_name or not isinstance(bucket_name, str):
        print(f"Invalid bucket_name: {bucket_name} (type: {type(bucket_name)})")
        return None

    try:
        # Reset file pointer to beginning
        file.seek(0)
        
        extra_args = {
            # "ACL": "public-read" if public else "private",
            "ContentType": file.content_type  # Important for PDFs
        }

        # Upload file - use file.file to get the file object
        s3.upload_fileobj(
            file.file if hasattr(file, 'file') else file,
            bucket_name,
            s3_path,
            ExtraArgs=extra_args
        )

        # Public URL (only works if ACL = public-read)
        if public:
            url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_path}"
            return url
        else:
            # If private, return a signed URL
            return get_signed_url(s3_path)

    except NoCredentialsError:
        print("AWS credentials not found!")
        return None
    except ClientError as e:
        print(f"Failed to upload file: {e}")
        return None
    except Exception as e:
        print(f"Something happened: {e}")
        import traceback
        traceback.print_exc()  # for more details
        return None