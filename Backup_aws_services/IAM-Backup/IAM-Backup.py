import boto3
import json
import os
from datetime import datetime
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install boto3
iam = boto3.client("iam")

BACKUP_DIR = f"iam-backup-{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(path, data):
    full_path = os.path.join(BACKUP_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=4, default=str)

# ---------------- USERS ----------------
print("Backing up IAM Users...")
users = iam.list_users()
save_json("users/users.json", users)

for user in users["Users"]:
    username = user["UserName"]

    attached = iam.list_attached_user_policies(UserName=username)
    save_json(f"users/{username}-attached.json", attached)

    inline = iam.list_user_policies(UserName=username)
    for policy_name in inline["PolicyNames"]:
        policy_doc = iam.get_user_policy(
            UserName=username,
            PolicyName=policy_name
        )
        save_json(f"users/{username}-inline-{policy_name}.json", 
policy_doc)

# ---------------- ROLES ----------------
print("Backing up IAM Roles...")
roles = iam.list_roles()
save_json("roles/roles.json", roles)

for role in roles["Roles"]:
    role_name = role["RoleName"]

    attached = iam.list_attached_role_policies(RoleName=role_name)
    save_json(f"roles/{role_name}-attached.json", attached)

    inline = iam.list_role_policies(RoleName=role_name)
    for policy_name in inline["PolicyNames"]:
        policy_doc = iam.get_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )
        save_json(f"roles/{role_name}-inline-{policy_name}.json", 
policy_doc)

# ---------------- GROUPS ----------------
print("Backing up IAM Groups...")
groups = iam.list_groups()
save_json("groups/groups.json", groups)

for group in groups["Groups"]:
    group_name = group["GroupName"]

    attached = iam.list_attached_group_policies(GroupName=group_name)
    save_json(f"groups/{group_name}-attached.json", attached)

    inline = iam.list_group_policies(GroupName=group_name)
    for policy_name in inline["PolicyNames"]:
        policy_doc = iam.get_group_policy(
            GroupName=group_name,
            PolicyName=policy_name
        )
        save_json(f"groups/{group_name}-inline-{policy_name}.json", 
policy_doc)

# ---------------- CUSTOMER MANAGED POLICIES ----------------
print("Backing up Customer Managed Policies...")
policies = iam.list_policies(Scope="Local")
save_json("policies/policies.json", policies)

for policy in policies["Policies"]:
    arn = policy["Arn"]
    name = policy["PolicyName"]

    meta = iam.get_policy(PolicyArn=arn)
    version = meta["Policy"]["DefaultVersionId"]

    doc = iam.get_policy_version(
        PolicyArn=arn,
        VersionId=version
    )
    save_json(f"policies/{name}.json", doc)

# ---------------- IDENTITY PROVIDERS ----------------
print("Backing up IAM Identity Providers...")

# SAML
saml = iam.list_saml_providers()
save_json("identity-providers/saml-providers.json", saml)

for provider in saml.get("SAMLProviderList", []):
    arn = provider["Arn"]
    saml_doc = iam.get_saml_provider(SAMLProviderArn=arn)
    save_json(
        f"identity-providers/saml-{arn.split('/')[-1]}.json",
        saml_doc
    )

# OIDC
oidc = iam.list_open_id_connect_providers()
save_json("identity-providers/oidc-providers.json", oidc)

for provider in oidc.get("OpenIDConnectProviderList", []):
    arn = provider["Arn"]
    oidc_doc = iam.get_open_id_connect_provider(
        OpenIDConnectProviderArn=arn
    )
    save_json(
        f"identity-providers/oidc-{arn.split('/')[-1]}.json",
        oidc_doc
    )

print(f"\n IAM BACKUP COMPLETED SUCCESSFULLY: {BACKUP_DIR}")

