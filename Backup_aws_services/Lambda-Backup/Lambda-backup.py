import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
BACKUP_DIR = f"lambda-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

def save_code(zip_bytes, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(zip_bytes)

# ---------- Get all regions ----------
ec2 = boto3.client("ec2")
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
save_json("regions.json", regions)

# ---------- Loop through regions ----------
for region in regions:
    print(f"\n Region: {region}")
    lam = boto3.client("lambda", region_name=region)

    # List all Lambda functions
    functions = []
    paginator = lam.get_paginator("list_functions")
    for page in paginator.paginate():
        functions.extend(page["Functions"])
    save_json(f"{region}/functions_list.json", functions)

    for fn in functions:
        fn_name = fn["FunctionName"]
        fn_arn = fn["FunctionArn"]
        print(f"   Lambda: {fn_name}")

        fn_dir = f"{BACKUP_DIR}/{region}/functions/{fn_name}"
        os.makedirs(fn_dir, exist_ok=True)

        # Function configuration
        config = lam.get_function_configuration(FunctionName=fn_name)
        save_json(f"{fn_dir}/config.json", config)

        # Tags
        try:
            tags = lam.list_tags(Resource=fn_arn)
            save_json(f"{fn_dir}/tags.json", tags)
        except:
            pass

        # Layers
        try:
            layers = config.get("Layers", [])
            save_json(f"{fn_dir}/layers.json", layers)
        except:
            pass

        # VPC config
        try:
            vpc = config.get("VpcConfig", {})
            save_json(f"{fn_dir}/vpc_config.json", vpc)
        except:
            pass

        # Download function code (zip)
        try:
            code_info = lam.get_function(FunctionName=fn_name)["Code"]
            zip_url = code_info.get("Location")
            if zip_url:
                import requests
                r = requests.get(zip_url)
                zip_path = f"{fn_dir}/{fn_name}.zip"
                save_code(r.content, zip_path)
        except Exception as e:
            print(f"   Cannot download zip: {e}")

print(f"\n FULL LAMBDA BACKUP COMPLETED: {BACKUP_DIR}")

