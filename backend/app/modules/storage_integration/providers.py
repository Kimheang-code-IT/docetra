import asyncio
from minio import Minio
from app.core.config import settings

async def test_provider(payload:dict)->dict:
    kind=str(payload.get("type") or "minio")
    if kind in {"minio","amazon_s3","cloudflare_r2"}:
        endpoint=str(payload.get("endpoint") or settings.s3_endpoint).removeprefix("http://").removeprefix("https://")
        secure=bool(payload.get("useSsl",payload.get("ssl",settings.s3_use_ssl)))
        client=Minio(endpoint,access_key=str(payload.get("accessKey") or settings.s3_access_key),secret_key=str(payload.get("secretKey") or settings.s3_secret_key),secure=secure,region=payload.get("region") or None)
        bucket=str(payload.get("bucket") or settings.s3_bucket)
        exists=await asyncio.to_thread(client.bucket_exists,bucket)
        if not exists: return {"status":"failed","message":f"Bucket {bucket} does not exist"}
        return {"status":"connected","message":f"Connected to {bucket}"}
    if kind=="local": return {"status":"failed","message":"Local filesystem storage is disabled in the read-only container; use MinIO/S3"}
    if kind=="google_drive":
        if not payload.get("folderId") or not (payload.get("clientId") or settings.google_drive_access_token): return {"status":"failed","message":"Google Drive credentials and folder are required"}
        return {"status":"connected","message":"Google Drive configuration is complete"}
    return {"status":"failed","message":"Unsupported storage provider"}
