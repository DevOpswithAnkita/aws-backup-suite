import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
cf = boto3.client("cloudfront")

BACKUP_DIR = f"cloudfront-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

print("Backing up CloudFront distributions...")

# -------- LIST DISTRIBUTIONS (pagination safe) --------
distributions = []
paginator = cf.get_paginator("list_distributions")

for page in paginator.paginate():
    dist_list = page.get("DistributionList", {})
    distributions.extend(dist_list.get("Items", []))

save_json("distributions/all_distributions.json", distributions)

if not distributions:
    print("No CloudFront distributions found")
    exit(0)

# -------- DISTRIBUTION DETAILS --------
for dist in distributions:
    dist_id = dist["Id"]
    domain = dist["DomainName"]

    print(f"→ Distribution: {dist_id} ({domain})")

    detail = cf.get_distribution(Id=dist_id)
    save_json(
        f"distributions/{dist_id}/distribution.json",
        detail
    )

    # Config (important for restore)
    config = cf.get_distribution_config(Id=dist_id)
    save_json(
        f"distributions/{dist_id}/config.json",
        config
    )

    # Tags
    arn = detail["Distribution"]["ARN"]
    tags = cf.list_tags_for_resource(Resource=arn)
    save_json(
        f"distributions/{dist_id}/tags.json",
        tags
    )

print(f"\n CLOUDFRONT BACKUP COMPLETED: {BACKUP_DIR}")

