import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
BACKUP_DIR = f"ec2-full-info-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# -------- GET REGIONS --------
ec2_global = boto3.client("ec2")
regions = [r["RegionName"] for r in 
ec2_global.describe_regions()["Regions"]]
save_json("regions.json", regions)

# -------- LOOP REGIONS --------
for region in regions:
    print(f"\n Region: {region}")
    ec2 = boto3.client("ec2", region_name=region)

    reservations = ec2.describe_instances()["Reservations"]
    if not reservations:
        continue

    for res in reservations:
        for inst in res["Instances"]:
            instance_id = inst["InstanceId"]
            print(f"  🖥 Instance: {instance_id}")

            # -------- BASIC INSTANCE INFO --------
            instance_info = {
                "InstanceId": instance_id,
                "InstanceType": inst["InstanceType"],
                "State": inst["State"]["Name"],
                "PrivateIp": inst.get("PrivateIpAddress"),
                "PublicIp": inst.get("PublicIpAddress"),
                "VpcId": inst.get("VpcId"),
                "SubnetId": inst.get("SubnetId"),
                "IamInstanceProfile": inst.get("IamInstanceProfile"),
                "Tags": inst.get("Tags", [])
            }

            save_json(
                f"{region}/instances/{instance_id}/instance.json",
                instance_info
            )

            # -------- ENI + SG RELATION --------
            enis_data = []
            for eni in inst.get("NetworkInterfaces", []):
                eni_info = {
                    "NetworkInterfaceId": eni["NetworkInterfaceId"],
                    "PrivateIp": eni.get("PrivateIpAddress"),
                    "SubnetId": eni.get("SubnetId"),
                    "VpcId": eni.get("VpcId"),
                    "Attachment": eni.get("Attachment"),
                    "SecurityGroups": eni.get("Groups")
                }
                enis_data.append(eni_info)

            save_json(
                f"{region}/instances/{instance_id}/enis.json",
                enis_data
            )

            # -------- SECURITY GROUP DETAILS --------
            sg_ids = set()
            for eni in inst.get("NetworkInterfaces", []):
                for sg in eni.get("Groups", []):
                    sg_ids.add(sg["GroupId"])

            for sg_id in sg_ids:
                sg_detail = ec2.describe_security_groups(
                    GroupIds=[sg_id]
                )["SecurityGroups"][0]

                save_json(
                    f"{region}/security-groups/{sg_id}.json",
                    sg_detail
                )

print(f"\n EC2 FULL INFO BACKUP COMPLETED: {BACKUP_DIR}")

