import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
route53 = boto3.client("route53")

BACKUP_DIR = f"route53-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ---------------- HOSTED ZONES ----------------
print("Backing up Route53 Hosted Zones...")

hosted_zones = []
paginator = route53.get_paginator("list_hosted_zones")

for page in paginator.paginate():
    hosted_zones.extend(page["HostedZones"])

save_json("hosted-zones/all_hosted_zones.json", hosted_zones)

# ---------------- RECORD SETS ----------------
for zone in hosted_zones:
    zone_id = zone["Id"].split("/")[-1]
    zone_name = zone["Name"]

    print(f"→ Hosted Zone: {zone_name} ({zone_id})")

    records = []
    paginator = route53.get_paginator("list_resource_record_sets")

    for page in paginator.paginate(HostedZoneId=zone_id):
        records.extend(page["ResourceRecordSets"])

    save_json(
        f"record-sets/{zone_name}_{zone_id}.json",
        records
    )

    # Hosted zone details
    hz_detail = route53.get_hosted_zone(Id=zone_id)
    save_json(
        f"hosted-zones/{zone_name}_{zone_id}_config.json",
        hz_detail
    )

# ---------------- HEALTH CHECKS ----------------
print("Backing up Route53 Health Checks...")

health_checks = []
paginator = route53.get_paginator("list_health_checks")

for page in paginator.paginate():
    health_checks.extend(page["HealthChecks"])

save_json("health-checks/all_health_checks.json", health_checks)

print(f"\n ROUTE53 BACKUP COMPLETED: {BACKUP_DIR}")

