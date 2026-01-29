import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
BACKUP_DIR = f"ecs-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)

ecs = boto3.client("ecs")

print("Listing ECS clusters...")
clusters = ecs.list_clusters()["clusterArns"]
save_json("clusters.json", clusters)

for cluster_arn in clusters:
    cluster_name = cluster_arn.split("/")[-1]
    print(f"\n Cluster: {cluster_name}")

    # Describe cluster
    cluster_detail = ecs.describe_clusters(
        clusters=[cluster_arn],
        include=["TAGS"]
    )
    save_json(f"clusters/{cluster_name}.json", cluster_detail)

    # List services
    services = ecs.list_services(cluster=cluster_arn)["serviceArns"]
    save_json(f"clusters/{cluster_name}/services_list.json", services)

    # Describe services (with tags)
    if services:
        services_detail = ecs.describe_services(
            cluster=cluster_arn,
            services=services,
            include=["TAGS"]
        )
        save_json(f"clusters/{cluster_name}/services.json", 
services_detail)

        # Backup task definitions
        for svc in services_detail["services"]:
            svc_name = svc["serviceName"]

            task_defs = 
ecs.list_task_definitions(familyPrefix=svc_name)["taskDefinitionArns"]

            for td in task_defs:
                td_detail = ecs.describe_task_definition(
                    taskDefinition=td,
                    include=["TAGS"]
                )
                td_name = 
td_detail["taskDefinition"]["taskDefinitionArn"].split("/")[1]
                save_json(f"taskDefinitions/{td_name}_backup.json", 
td_detail)

print(f"\n FULL ECS BACKUP COMPLETED: {BACKUP_DIR}")

