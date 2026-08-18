import asyncio
import re
from io import BytesIO
from minio import Minio
from app.core.config import settings

client=Minio(settings.s3_endpoint.removeprefix("http://").removeprefix("https://"),access_key=settings.s3_access_key,secret_key=settings.s3_secret_key,secure=settings.s3_use_ssl)
async def ensure_bucket():
    exists=await asyncio.to_thread(client.bucket_exists,settings.s3_bucket)
    if not exists: await asyncio.to_thread(client.make_bucket,settings.s3_bucket)
async def put_bytes(key:str,data:bytes,content_type:str):
    await ensure_bucket(); await asyncio.to_thread(client.put_object,settings.s3_bucket,key,BytesIO(data),len(data),content_type=content_type)
async def delete_object(key:str): await asyncio.to_thread(client.remove_object,settings.s3_bucket,key)
def safe_name(value:str): return re.sub(r"[^A-Za-z0-9._-]","_",value)[:180] or "file"
