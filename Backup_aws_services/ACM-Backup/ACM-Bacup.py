import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
BACKUP_DIR = f"acm-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# -------- GET ALL REGIONS --------
ec2 = boto3.client("ec2")
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
save_json("regions.json", regions)

print(f"Regions found: {regions}")

# -------- LOOP REGIONS --------
for region in regions:
    print(f"\n Region: {region}")
    acm = boto3.client("acm", region_name=region)

    paginator = acm.get_paginator("list_certificates")
    certs = []

    for page in paginator.paginate(
        CertificateStatuses=[
            "PENDING_VALIDATION",
            "ISSUED",
            "INACTIVE",
            "EXPIRED",
            "VALIDATION_TIMED_OUT",
            "REVOKED",
            "FAILED"
        ]
    ):
        certs.extend(page.get("CertificateSummaryList", []))

    if not certs:
        print("  No certificates found")
        continue

    save_json(f"{region}/certificates_list.json", certs)

    for cert in certs:
        arn = cert["CertificateArn"]
        print(f"  Certificate: {arn}")

        # Describe certificate
        detail = acm.describe_certificate(CertificateArn=arn)
        save_json(
            f"{region}/certificates/{arn.split('/')[-1]}.json",
            detail
        )

        # Tags
        tags = acm.list_tags_for_certificate(CertificateArn=arn)
        save_json(
            f"{region}/certificates/{arn.split('/')[-1]}-tags.json",
            tags
        )

print(f"\n ACM BACKUP COMPLETED (ALL REGIONS): {BACKUP_DIR}")

