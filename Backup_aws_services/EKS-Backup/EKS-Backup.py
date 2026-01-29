import boto3
import json
import os
import subprocess
from datetime import datetime

BACKUP_DIR = f"eks-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4, default=str)

# -------- GET ALL REGIONS --------
ec2 = boto3.client("ec2")
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
save_json("regions.json", regions)

print(f"Regions found: {regions}")

# -------- LOOP REGIONS --------
for region in regions:
    print(f"\n Region: {region}")
    eks = boto3.client("eks", region_name=region)

    try:
        clusters = eks.list_clusters()["clusters"]
    except Exception as e:
        print(f"   Cannot access EKS in {region}: {e}")
        continue

    if not clusters:
        print("  No EKS clusters found")
        continue

    save_json(f"{region}/clusters.json", clusters)

    for cluster_name in clusters:
        print(f"  Cluster: {cluster_name}")

        cluster = eks.describe_cluster(name=cluster_name)
        save_json(f"{region}/clusters/{cluster_name}.json", cluster)

        # -------- NODE GROUPS --------
        nodegroups = eks.list_nodegroups(clusterName=cluster_name)
        save_json(
            f"{region}/nodegroups/{cluster_name}-nodegroups.json",
            nodegroups
        )

        for ng in nodegroups.get("nodegroups", []):
            ng_detail = eks.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng
            )
            save_json(
                f"{region}/nodegroups/{cluster_name}-{ng}.json",
                ng_detail
            )

        # -------- FARGATE --------
        fargate = eks.list_fargate_profiles(clusterName=cluster_name)
        save_json(
            f"{region}/fargate/{cluster_name}-profiles.json",
            fargate
        )

        for fp in fargate.get("fargateProfileNames", []):
            fp_detail = eks.describe_fargate_profile(
                clusterName=cluster_name,
                fargateProfileName=fp
            )
            save_json(
                f"{region}/fargate/{cluster_name}-{fp}.json",
                fp_detail
            )

        # -------- KUBERNETES YAML --------
        print("    ⎈ Backing up Kubernetes resources")

        k8s_dir = f"{BACKUP_DIR}/{region}/k8s/{cluster_name}"
        os.makedirs(k8s_dir, exist_ok=True)

        # update kubeconfig for this cluster
        subprocess.run(
            f"aws eks update-kubeconfig --name {cluster_name} --region 
{region}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        resources = [
            "ns", "deploy", "sts", "ds",
            "svc", "ingress", "cm",
            "secret", "pvc", "sa",
            "role", "rolebinding",
            "clusterrole", "clusterrolebinding"
        ]

        for res in resources:
            outfile = f"{k8s_dir}/{res}.yaml"
            subprocess.run(
                f"kubectl get {res} --all-namespaces -o yaml > {outfile}",
                shell=True
            )

print(f"\n EKS BACKUP COMPLETED: {BACKUP_DIR}")

