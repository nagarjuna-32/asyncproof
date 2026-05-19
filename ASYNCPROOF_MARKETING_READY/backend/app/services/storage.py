import os
import shutil
from pathlib import Path


def store_recording(local_path: str) -> dict:
    """
    Secure storage router.
    Production recommendation: use S3-compatible object storage, Cloudinary, or Supabase Storage.
    Local storage is development-only.
    """
    provider = os.getenv("STORAGE_PROVIDER", "local").lower().strip()
    file_name = Path(local_path).name

    if provider == "s3":
        try:
            import boto3
            bucket = os.environ["S3_BUCKET"]
            key = f"recordings/{file_name}"
            client = boto3.client(
                "s3",
                region_name=os.getenv("AWS_REGION", "ap-south-1") or None,
            )
            client.upload_file(local_path, bucket, key, ExtraArgs={"ACL": "private"})
            return {"storage_provider": "s3", "storage_url": f"s3://{bucket}/{key}", "storage_key": key}
        except Exception as e:
            return {"storage_provider": "local", "storage_url": None, "storage_error": str(e)}

    if provider == "supabase":
        # Use Supabase signed-upload/storage API in production. This keeps app install lightweight.
        return {
            "storage_provider": "supabase",
            "storage_url": None,
            "storage_error": "Configure SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and implement signed upload.",
        }

    if provider == "cloudinary":
        return {
            "storage_provider": "cloudinary",
            "storage_url": None,
            "storage_error": "Configure CLOUDINARY_URL and implement video upload through Cloudinary SDK/API.",
        }

    # Development fallback only.
    safe_dir = Path(os.getenv("LOCAL_UPLOAD_DIR", "uploads"))
    safe_dir.mkdir(exist_ok=True)
    dest = safe_dir / file_name
    if Path(local_path).resolve() != dest.resolve():
        shutil.copy2(local_path, dest)
    return {"storage_provider": "local", "storage_url": str(dest)}
