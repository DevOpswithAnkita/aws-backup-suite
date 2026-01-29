import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
s3 = boto3.client("s3")

BACKUP_DIR = f"s3-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

print("Backing up all S3 buckets...")

# List all buckets
buckets = s3.list_buckets()["Buckets"]
save_json("buckets_list.json", buckets)

for b in buckets:
    bucket_name = b["Name"]
    print(f"→ Bucket: {bucket_name}")

    # Get bucket region
    try:
        region = 
s3.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or 
"us-east-1"
    except Exception as e:
        print(f"   Cannot get region: {e}")
        region = "unknown"

    bucket_dir = f"{BACKUP_DIR}/{bucket_name}"
    os.makedirs(bucket_dir, exist_ok=True)

    # Versioning
    try:
        versioning = s3.get_bucket_versioning(Bucket=bucket_name)
        save_json(f"{bucket_dir}/versioning.json", versioning)
    except:
        pass

    # Encryption
    try:
        encryption = s3.get_bucket_encryption(Bucket=bucket_name)
        save_json(f"{bucket_dir}/encryption.json", encryption)
    except:
        pass

    # Policy
    try:
        policy = s3.get_bucket_policy(Bucket=bucket_name)
        save_json(f"{bucket_dir}/policy.json", policy)
    except:
        pass

    # Tags
    try:
        tags = s3.get_bucket_tagging(Bucket=bucket_name)
        save_json(f"{bucket_dir}/tags.json", tags)
    except:
        pass

    # Lifecycle
    try:
        lifecycle = 
s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        save_json(f"{bucket_dir}/lifecycle.json", lifecycle)
    except:
        pass

    # Public access block
    try:
        pab = s3.get_public_access_block(Bucket=bucket_name)
        save_json(f"{bucket_dir}/public_access_block.json", pab)
    except:
        pass

    # Optional: List objects (comment if huge)
    try:
        objs = []
        paginator = boto3.client("s3").get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name):
            objs.extend(page.get("Contents", []))
        save_json(f"{bucket_dir}/objects.json", objs)
    except:
        pass

print(f"\n S3 BACKUP COMPLETED: {BACKUP_DIR}")

