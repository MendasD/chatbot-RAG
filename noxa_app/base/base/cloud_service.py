from dotenv import load_dotenv
import os
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# Charger le .env (priorité aux variables d'environnement système)
# On ne charge le .env que si on n'est pas déjà dans un environnement configuré (ex: local dev)
if not os.getenv('AWS_ACCESS_KEY_ID'):
    BASE_DIR = Path(__file__).resolve().parent
    print(f"BASE_DIR set to: {BASE_DIR}")
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    load_dotenv() # Fallback to CWD .env

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID') 
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_REGION', 'eu-north-1')
bucket_name = os.getenv('BUCKET_NAME', 'nlp-rag-bucket') # nlp-rag-bucket

# Debug (safe version)
if os.getenv('DEBUG', 'True') == 'True':
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

# get a pre-signed url for a pdf
def get_signed_url(s3_key, expiration=3600):
    """Generate a presigned URL for private S3 objects"""
     
    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket_name, 
                "Key": s3_key,  # ex: documents/memoires/monfichier.pdf
            },
            ExpiresIn=expiration,  
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
    


########################################################################
########################################################################
########################################################################

### USE OF CLOUDINARY ##########

def upload_file_cloudinary(file_type="image", file=None, public_id=None, folder=None, **kwargs):
    """
    Upload a file to Cloudinary and return the URL.
    
    :param file_type: 'image' or 'raw' (for PDFs, etc.)
    :param file: Django UploadedFile object to upload
    :param public_id: Custom public ID for the file (optional)
    :param folder: Folder path in Cloudinary (optional)
    :param kwargs: Additional parameters for Cloudinary uploader
    :return: URL of the uploaded file or None
    """
    import cloudinary
    import cloudinary.uploader
    from cloudinary.utils import cloudinary_url
    from .cloudinary_config import configure_cloudinary

    # Configuration
    configure_cloudinary()

    try:
        # Prepare upload options
        upload_options = {
            "resource_type": file_type,
            "public_id": public_id,
            "folder": folder,
            "access_mode": "public",
            **kwargs
        }

        # Remove None values
        upload_options = {k: v for k, v in upload_options.items() if v is not None}

        # Upload file
        if file:
            upload_result = cloudinary.uploader.upload(file, **upload_options)
        else:
            # If no file provided, you might want to handle that case
            raise ValueError("No file provided for upload")

        # Return the secure URL
        return upload_result.get("secure_url")

    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None


if __name__ == "__main__":
    CLOUDINARY_URL = "cloudinary://732974968223895:t6rzUL2tnGvmxzkelPF3zsVp-YY@dsupmimkx"
    API_SECRET = "t6rzUL2tnGvmxzkelPF3zsVp-YY"
    API_KEY = "732974968223895"
    CLOUD_NAME = "dsupmimkx"

    import cloudinary
    import cloudinary.uploader
    from cloudinary.utils import cloudinary_url

    # Configuration       
    cloudinary.config( 
        cloud_name = "dsupmimkx", 
        api_key = "732974968223895", 
        api_secret = API_SECRET, # Click 'View API Keys' above to copy your API secret
        secure=True
    )

    # Upload an image
    upload_result = cloudinary.uploader.upload("data/raw/stage_immersion_David_Christ_AS3.pdf",
                                            public_id="mon_pdf", resource_type="image", folder="documents/memoires")
    print(f'secure_url : {upload_result["secure_url"]}')

    url = upload_result["secure_url"].replace(
    "/upload/",
    "/upload/fl_attachment/"
    )

    print(url)

    # Optimize delivery by resizing and applying auto-format and auto-quality
    # optimize_url, _ = cloudinary_url("clusters", fetch_format="auto", quality="auto")
    # print(optimize_url)

    # # Transform the image: auto-crop to square aspect_ratio
    # auto_crop_url, _ = cloudinary_url("clusters", width=500, height=500, crop="auto", gravity="auto")
    # print(auto_crop_url)
