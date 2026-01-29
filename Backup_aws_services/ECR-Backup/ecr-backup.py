import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
BACKUP_DIR = f"ecr-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ---------- Get all regions ----------
ec2 = boto3.client("ec2")
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
save_json("regions.json", regions)

# ---------- Loop through regions ----------
for region in regions:
    print(f"\n Region: {region}")
    ecr = boto3.client("ecr", region_name=region)

    # List all repositories
    repos = ecr.describe_repositories()["repositories"]
    save_json(f"{region}/repositories.json", repos)

    for repo in repos:
        repo_name = repo["repositoryName"]
        print(f"   Repository: {repo_name}")

        repo_dir = f"{BACKUP_DIR}/{region}/repositories/{repo_name}"
        os.makedirs(repo_dir, exist_ok=True)

        # Save repository details
        save_json(f"{repo_dir}/repo_details.json", repo)

        # Tags
        try:
            tags = ecr.list_tags_for_resource(
                resourceArn=repo["repositoryArn"]
            )
            save_json(f"{repo_dir}/tags.json", tags)
        except:
            pass

        # Lifecycle policy
        try:
            lifecycle = ecr.get_lifecycle_policy(repositoryName=repo_name)
            save_json(f"{repo_dir}/lifecycle_policy.json", lifecycle)
        except e:
            print(f"    ⚠ No lifecycle policy: {e}")

        # Image scan configuration
        try:
            scan_config = ecr.describe_registry()["registryId"]
            # Or for image scan settings per repo
            scan_settings = 
ecr.describe_repositories(repositoryNames=[repo_name])
            save_json(f"{repo_dir}/scan_config.json", scan_settings)
        except:
            pass

        # List all images (tags + digest)
        images = []
        paginator = ecr.get_paginator("list_images")
        for page in paginator.paginate(repositoryName=repo_name, 
filter={"tagStatus": "ANY"}):
            images.extend(page.get("imageIds", []))
        save_json(f"{repo_dir}/images.json", images)

print(f"\n FULL ECR BACKUP COMPLETED: {BACKUP_DIR}")

