#!/usr/bin/env python3
import time
import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
from botocore.config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

LOCAL_DIR = Path(__file__).parent.parent / "ressources"

ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "your-account-id")
ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID", "your-access-key")
SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "your-secret-key")
BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "your-bucket-name")
JURISDICTION = os.getenv("R2_JURISDICTION", "")

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "8"))
PREFIX = ""


ENDPOINT_HOST = f"{ACCOUNT_ID}.{JURISDICTION + '.' if JURISDICTION else ''}r2.cloudflarestorage.com"

session = boto3.session.Session()
s3 = session.client(
    service_name="s3",
    endpoint_url=f"https://{ENDPOINT_HOST}",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def list_all_keys(bucket, prefix=""):
    """Yield every object key in the bucket (handles pagination)."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"]


def download_one(bucket, key, local_dir):
    local_path = local_dir / key
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Skip if already downloaded (lets you resume interrupted runs)
    if local_path.exists():
        return f"SKIP  {key}"

    s3.download_file(bucket, key, str(local_path))
    return f"OK    {key}"


def chunked(iterable, size):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    start_time = time.perf_counter()
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Listing objects in bucket '{BUCKET_NAME}' (prefix='{PREFIX}')...")
    all_keys = list(list_all_keys(BUCKET_NAME, PREFIX))
    total = len(all_keys)
    print(f"Found {total} objects. Downloading in batches of {BATCH_SIZE}...\n")

    done = 0
    for batch_num, batch in enumerate(chunked(all_keys, BATCH_SIZE), start=1):
        print(f"--- Batch {batch_num} ({len(batch)} objects) ---")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(download_one, BUCKET_NAME, key, LOCAL_DIR): key
                for key in batch
            }
            for future in as_completed(futures):
                key = futures[future]
                try:
                    result = future.result()
                    print(result)
                except Exception as e:
                    print(f"FAIL  {key}: {e}")

        done += len(batch)
        print(f"Progress: {done}/{total}\n")

    end_time = time.perf_counter()
    elapsed_seconds = end_time - start_time
    print(f"All done in {elapsed_seconds:.2f} seconds.")

if __name__ == "__main__":
    main()
