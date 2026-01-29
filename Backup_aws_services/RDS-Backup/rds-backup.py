import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
# --------- Setup backup directory ----------
BACKUP_DIR = f"RDS-Backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    """Helper function to save JSON files"""
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

# --------- Get all AWS regions ----------
ec2 = boto3.client("ec2")
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
save_json("regions.json", regions)

# --------- Loop through all regions ----------
for region in regions:
    print(f"\n Region: {region}")
    rds = boto3.client("rds", region_name=region)

    # --------- DB Instances ---------
    instances = rds.describe_db_instances()["DBInstances"]
    save_json(f"{region}/db_instances.json", instances)

    for db in instances:
        db_id = db["DBInstanceIdentifier"]
        db_arn = db["DBInstanceArn"]
        print(f"   DB Instance: {db_id}")

        # Collect all metadata
        instance_info = {
            "DBInstanceIdentifier": db_id,
            "DBInstanceClass": db["DBInstanceClass"],
            "Engine": db["Engine"],
            "EngineVersion": db["EngineVersion"],
            "MultiAZ": db["MultiAZ"],
            "AllocatedStorage": db["AllocatedStorage"],
            "StorageType": db["StorageType"],
            "PubliclyAccessible": db["PubliclyAccessible"],
            "VpcSecurityGroups": db.get("VpcSecurityGroups"),
            "DBSubnetGroup": db.get("DBSubnetGroup"),
            "Endpoint": db.get("Endpoint"),
            "ReadReplicaDBInstanceIdentifiers": 
db.get("ReadReplicaDBInstanceIdentifiers", []),
            "PreferredMaintenanceWindow": 
db.get("PreferredMaintenanceWindow"),
            "BackupRetentionPeriod": db.get("BackupRetentionPeriod"),
            "StorageEncrypted": db.get("StorageEncrypted"),
            "IAMDatabaseAuthenticationEnabled": 
db.get("IAMDatabaseAuthenticationEnabled", False)
        }

        save_json(f"{region}/db_instances/{db_id}_info.json", 
instance_info)

        # Tags
        try:
            tags = rds.list_tags_for_resource(ResourceName=db_arn)
            save_json(f"{region}/db_instances/{db_id}_tags.json", tags)
        except:
            pass

    # --------- DB Clusters (Aurora) ---------
    clusters = rds.describe_db_clusters().get("DBClusters", [])
    save_json(f"{region}/db_clusters.json", clusters)

    for cluster in clusters:
        cluster_id = cluster["DBClusterIdentifier"]
        cluster_arn = cluster["DBClusterArn"]
        print(f"  DB Cluster: {cluster_id}")

        cluster_info = {
            "DBClusterIdentifier": cluster_id,
            "Engine": cluster["Engine"],
            "EngineVersion": cluster["EngineVersion"],
            "Endpoint": cluster["Endpoint"],
            "ReaderEndpoint": cluster.get("ReaderEndpoint"),
            "MultiAZ": cluster.get("MultiAZ"),
            "VpcSecurityGroups": cluster.get("VpcSecurityGroups"),
            "DBSubnetGroup": cluster.get("DBSubnetGroup"),
            "DatabaseName": cluster.get("DatabaseName"),
            "PreferredMaintenanceWindow": 
cluster.get("PreferredMaintenanceWindow"),
            "BackupRetentionPeriod": cluster.get("BackupRetentionPeriod"),
            "StorageEncrypted": cluster.get("StorageEncrypted")
        }
        save_json(f"{region}/db_clusters/{cluster_id}_info.json", 
cluster_info)

        # Tags
        try:
            tags = rds.list_tags_for_resource(ResourceName=cluster_arn)
            save_json(f"{region}/db_clusters/{cluster_id}_tags.json", 
tags)
        except:
            pass

        # RDS Proxies linked to cluster
        proxies = rds.describe_db_proxies()["DBProxies"]
        for proxy in proxies:
            if proxy.get("AssociatedClusters") and cluster_id in 
proxy["AssociatedClusters"]:
                
save_json(f"{region}/db_clusters/{cluster_id}_proxy_{proxy['DBProxyName']}.json", 
proxy)

    # --------- Option Groups ---------
    option_groups = rds.describe_option_groups()["OptionGroupsList"]
    save_json(f"{region}/option_groups.json", option_groups)

print(f"\n FULL RDS AUDIT BACKUP COMPLETED: {BACKUP_DIR}")

