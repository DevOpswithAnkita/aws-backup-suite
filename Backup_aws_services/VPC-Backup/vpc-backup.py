import boto3
import json
import os
from datetime import datetime
import yaml  
# python3 -m venv venv
# source venv/bin/activate      # Linux / Mac
# venv\Scripts\activate         # Windows
# pip install pyyaml boto3
# Ensure backup directory exists
backup_dir = "vpc_backup"
os.makedirs(backup_dir, exist_ok=True)

# Function to convert datetime objects to string
def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# Initialize EC2 client to list all regions
ec2_client = boto3.client("ec2")
regions_response = ec2_client.describe_regions()
regions = [r['RegionName'] for r in regions_response['Regions']]

# Loop through each region
for region in regions:
    print(f"Fetching VPC info in region: {region}")
    ec2 = boto3.client("ec2", region_name=region)
    
    # Fetch all VPCs
    vpcs_response = ec2.describe_vpcs()
    vpcs = vpcs_response["Vpcs"]
    
    if not vpcs:
        print(f"No VPCs found in region {region}")
        continue
    
    region_backup = {}

    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        print(f"Processing VPC: {vpc_id}")
        vpc_data = {}
        
        # Add VPC
        vpc_data["VPC"] = vpc

        # Subnets
        subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", 
"Values": [vpc_id]}])["Subnets"]
        vpc_data["Subnets"] = subnets

        # Route Tables
        route_tables = ec2.describe_route_tables(Filters=[{"Name": 
"vpc-id", "Values": [vpc_id]}])["RouteTables"]
        vpc_data["RouteTables"] = route_tables

        # Internet Gateways
        igws = ec2.describe_internet_gateways(Filters=[{"Name": 
"attachment.vpc-id", "Values": [vpc_id]}])["InternetGateways"]
        vpc_data["InternetGateways"] = igws

        # NAT Gateways
        nat_gateways = ec2.describe_nat_gateways(Filters=[{"Name": 
"vpc-id", "Values": [vpc_id]}])["NatGateways"]
        vpc_data["NATGateways"] = nat_gateways

        # Security Groups
        sgs = ec2.describe_security_groups(Filters=[{"Name": "vpc-id", 
"Values": [vpc_id]}])["SecurityGroups"]
        vpc_data["SecurityGroups"] = sgs

        # Network ACLs
        nacls = ec2.describe_network_acls(Filters=[{"Name": "vpc-id", 
"Values": [vpc_id]}])["NetworkAcls"]
        vpc_data["NetworkACLs"] = nacls

        # Elastic IPs (associated only)
        eips = ec2.describe_addresses()["Addresses"]
        associated_eips = [eip for eip in eips if "AssociationId" in eip]
        vpc_data["ElasticIPs"] = associated_eips

        # VPC Peering Connections (requester)
        peerings = ec2.describe_vpc_peering_connections(Filters=[{"Name": 
"requester-vpc-info.vpc-id", "Values": 
[vpc_id]}])["VpcPeeringConnections"]
        vpc_data["VPCPeeringConnections"] = peerings

        region_backup[vpc_id] = vpc_data

    # Save YAML
    yaml_file = os.path.join(backup_dir, f"{region}_vpc_backup.yaml")
    with open(yaml_file, "w") as f:
        yaml.dump(region_backup, f, sort_keys=False, 
default_flow_style=False)

    print(f"Backup completed for region {region}. Saved to {yaml_file}\n")

print("All regions backup completed!")

