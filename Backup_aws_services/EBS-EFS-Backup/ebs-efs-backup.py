import boto3
import json
import os
from datetime import datetime

BACKUP_DIR = f"storage-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# ---------- GET REGIONS ----------
ec2_global = boto3.client("ec2")
regions = [r["RegionName"] for r in 
ec2_global.describe_regions()["Regions"]]
save_json("regions.json", regions)

# ---------- LOOP REGIONS ----------
for region in regions:
    print(f"\n Region: {region}")

    ec2 = boto3.client("ec2", region_name=region)
    efs = boto3.client("efs", region_name=region)

    # ================= EBS =================
    print("   Backing up EBS volumes")

    volumes = ec2.describe_volumes()["Volumes"]
    for vol in volumes:
        vol_id = vol["VolumeId"]
        save_json(f"{region}/ebs/volumes/{vol_id}.json", vol)

        # OPTIONAL snapshot (comment if not needed)
        snapshot = ec2.create_snapshot(
            VolumeId=vol_id,
            Description=f"Auto-backup {vol_id} {datetime.now()}"
        )
        save_json(
            f"{region}/ebs/snapshots/{snapshot['SnapshotId']}.json",
            snapshot
        )

    # ================= EFS =================
    print("   Backing up EFS file systems")

    filesystems = efs.describe_file_systems()["FileSystems"]
    for fs in filesystems:
        fs_id = fs["FileSystemId"]

        save_json(
            f"{region}/efs/filesystems/{fs_id}.json",
            fs
        )

        # Tags
        tags = efs.list_tags_for_resource(ResourceId=fs_id)
        save_json(
            f"{region}/efs/filesystems/{fs_id}-tags.json",
            tags
        )

        # Mount targets
        mts = efs.describe_mount_targets(FileSystemId=fs_id)
        save_json(
            f"{region}/efs/mount-targets/{fs_id}.json",
            mts
        )

        # Mount target security groups
        for mt in mts["MountTargets"]:
            mt_id = mt["MountTargetId"]
            sgs = efs.describe_mount_target_security_groups(
                MountTargetId=mt_id
            )
            save_json(
                f"{region}/efs/mount-targets/{mt_id}-sgs.json",
                sgs
            )

print(f"\n EBS + EFS BACKUP COMPLETED: {BACKUP_DIR}")

