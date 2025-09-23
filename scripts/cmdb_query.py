#!/usr/bin/env python3
import requests
import json
import os
import sys
from urllib.parse import urljoin

# ServiceNow configuration
SN_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
SN_USERNAME = os.getenv('SERVICENOW_USERNAME')
SN_PASSWORD = os.getenv('SERVICENOW_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    print("Error: Missing required ServiceNow environment variables")
    print("Required: SERVICENOW_INSTANCE, SERVICENOW_USERNAME, SERVICENOW_PASSWORD")
    sys.exit(1)

# Base URL for ServiceNow API
BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now"

# Common headers for API requests
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Authentication
AUTH = (SN_USERNAME, SN_PASSWORD)

def make_request(endpoint, params=None, method='GET'):
    """Make authenticated request to ServiceNow API"""
    url = urljoin(BASE_URL, endpoint)
    
    try:
        if method == 'GET':
            response = requests.get(url, auth=AUTH, headers=HEADERS, params=params)
        elif method == 'POST':
            response = requests.post(url, auth=AUTH, headers=HEADERS, json=params)
        elif method == 'PUT':
            response = requests.put(url, auth=AUTH, headers=HEADERS, json=params)
        elif method == 'DELETE':
            response = requests.delete(url, auth=AUTH, headers=HEADERS)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {str(e)}")
        sys.exit(1)

# CMDB Query Tool
import argparse

parser = argparse.ArgumentParser(description='Query ServiceNow CMDB for servers')
parser.add_argument('application_id', help='Application sys_id or name to query servers for')
args = parser.parse_args()

application_id = args.application_id

print(f"Querying CMDB for servers linked to application: {application_id}")
print("")

# First, get the application details
print("=== Application Details ===")
# Simple search patterns for better matching
search_patterns = [
    f'sys_id={application_id}',  # Exact sys_id match
    f'name={application_id}',    # Exact name match
    f'nameLIKE{application_id}', # Partial name match
]

app_params = {
    'sysparm_query': '^OR'.join(search_patterns),
    'sysparm_fields': 'sys_id,name,short_description,operational_status,assigned_to,owned_by',
    'sysparm_limit': 10
}

try:
    app_results = make_request('table/cmdb_ci_appl', app_params)
    if not app_results.get('result'):
        print(f"❌ Application not found: {application_id}")
        print("💡 Suggestions:")
        print("   - Check the application name spelling")
        print("   - Try a partial name (e.g., 'XYZ' instead of 'XYZ App')")
        print("   - Contact your ServiceNow administrator")
        sys.exit(1)
    
    apps = app_results['result']
    
    # Handle multiple matches
    if len(apps) > 1:
        print(f"🔍 Found {len(apps)} applications matching '{application_id}':")
        print("")
        for i, app in enumerate(apps, 1):
            print(f"{i}. {app.get('name', 'N/A')} (ID: {app.get('sys_id', 'N/A')})")
            print(f"   Description: {app.get('short_description', 'N/A')}")
            print(f"   Status: {app.get('operational_status', 'N/A')}")
            print(f"   Assigned to: {app.get('assigned_to', 'N/A')}")
            print(f"   Owned by: {app.get('owned_by', 'N/A')}")
            print("")
        
        print("❌ Multiple applications found. Please specify which one:")
        print("   - Use the exact application name")
        print("   - Use the sys_id (e.g., 'abc123def456')")
        print("   - Use a more specific search term")
        sys.exit(1)
    
    # Single match found
    app = apps[0]
    app_sys_id = app.get('sys_id')
    print(f"✅ Found application: {app.get('name', 'N/A')} (ID: {app_sys_id})")
    print(f"Description: {app.get('short_description', 'N/A')}")
    print(f"Status: {app.get('operational_status', 'N/A')}")
    print(f"Assigned to: {app.get('assigned_to', 'N/A')}")
    print(f"Owned by: {app.get('owned_by', 'N/A')}")
    print("")
    
except Exception as e:
    print(f"❌ Error finding application: {str(e)}")
    sys.exit(1)

# Query servers through CMDB relationships
print("=== Servers Linked to Application via CMDB Relationships ===")
# First, find all CIs related to the application
relationship_params = {
    'sysparm_query': f'parent={app_sys_id}^type=Used by^ORparent={app_sys_id}^type=Uses^ORparent={app_sys_id}^type=Hosted on^ORparent={app_sys_id}^type=Hosts^ORparent={app_sys_id}^type=Runs on',
    'sysparm_fields': 'sys_id,parent,child,type',
    'sysparm_limit': 100
}

try:
    relationship_results = make_request('table/cmdb_rel_ci', relationship_params)
    if relationship_results.get('result'):
        print(f"Found {len(relationship_results['result'])} relationships for application")
        
        # Collect all related CI IDs
        related_ci_ids = [rel.get('child') for rel in relationship_results['result'] if rel.get('child')]
        
        if related_ci_ids:
            # Query servers from the related CIs
            server_query = '^OR'.join([f'sys_id={ci_id}' for ci_id in related_ci_ids])
            server_params = {
                'sysparm_query': f'class_name=cmdb_ci_server^{server_query}',
                'sysparm_fields': 'sys_id,name,host_name,ip_address,state,operational_status,os_name,os_version,cpu_count,ram,disk_space,location,assigned_to,owned_by,serial_number,asset_tag',
                'sysparm_limit': 100
            }
            
            server_results = make_request('table/cmdb_ci', server_params)
            if server_results.get('result'):
                print(f"Found {len(server_results['result'])} servers linked to application:")
                for server in server_results['result']:
                    print(f"  Server: {server.get('name', 'N/A')} (ID: {server.get('sys_id', 'N/A')})")
                    print(f"    Hostname: {server.get('host_name', 'N/A')}")
                    print(f"    IP Address: {server.get('ip_address', 'N/A')}")
                    print(f"    State: {server.get('state', 'N/A')}, Status: {server.get('operational_status', 'N/A')}")
                    print(f"    OS: {server.get('os_name', 'N/A')} {server.get('os_version', 'N/A')}")
                    print(f"    Hardware: {server.get('cpu_count', 'N/A')} CPUs, {server.get('ram', 'N/A')} RAM, {server.get('disk_space', 'N/A')} Disk")
                    print(f"    Location: {server.get('location', 'N/A')}")
                    print(f"    Assigned to: {server.get('assigned_to', 'N/A')}")
                    print(f"    Owned by: {server.get('owned_by', 'N/A')}")
                    print(f"    Serial: {server.get('serial_number', 'N/A')}, Asset Tag: {server.get('asset_tag', 'N/A')}")
                    print("")
            else:
                print("No servers found in related CIs")
        else:
            print("No related CIs found")
    else:
        print("No relationships found for application")
    print("")
except Exception as e:
    print(f"Error querying relationships: {str(e)}")

# Query servers through services
print("=== Servers Through Services ===")
# First get services for the application
service_params = {
    'sysparm_query': f'application={app_sys_id}',
    'sysparm_fields': 'sys_id,name',
    'sysparm_limit': 50
}

try:
    service_results = make_request('table/apm_service', service_params)
    if service_results.get('result'):
        service_ids = [service['sys_id'] for service in service_results['result']]
        print(f"Found {len(service_ids)} services for application")
        
        # Query servers for each service
        for service in service_results['result']:
            service_id = service['sys_id']
            service_name = service.get('name', 'N/A')
            
            service_server_params = {
                'sysparm_query': f'service={service_id}',
                'sysparm_fields': 'sys_id,name,host_name,ip_address,state,operational_status,os_name,os_version',
                'sysparm_limit': 50
            }
            
            try:
                service_server_results = make_request('table/cmdb_ci_server', service_server_params)
                if service_server_results.get('result'):
                    print(f"  Service '{service_name}' has {len(service_server_results['result'])} servers:")
                    for server in service_server_results['result']:
                        print(f"    - {server.get('name', 'N/A')} ({server.get('host_name', 'N/A')}) - {server.get('ip_address', 'N/A')}")
                        print(f"      State: {server.get('state', 'N/A')}, OS: {server.get('os_name', 'N/A')}")
            except Exception as e:
                print(f"    Error querying servers for service {service_name}: {str(e)}")
    else:
        print("No services found for application")
    print("")
except Exception as e:
    print(f"Error querying services: {str(e)}")

# Query AWS-specific information if available
print("=== AWS Information ===")
aws_params = {
    'sysparm_query': f'application={app_sys_id}',
    'sysparm_fields': 'sys_id,name,host_name,aws_account_id,aws_region,aws_instance_id,aws_instance_type,aws_availability_zone,aws_vpc_id,aws_subnet_id,aws_security_groups,aws_tags',
    'sysparm_limit': 100
}

try:
    aws_results = make_request('table/cmdb_ci_aws_instance', aws_params)
    if aws_results.get('result'):
        print(f"Found {len(aws_results['result'])} AWS instances linked to application:")
        for aws_instance in aws_results['result']:
            print(f"  AWS Instance: {aws_instance.get('name', 'N/A')} (ID: {aws_instance.get('sys_id', 'N/A')})")
            print(f"    Instance ID: {aws_instance.get('aws_instance_id', 'N/A')}")
            print(f"    Type: {aws_instance.get('aws_instance_type', 'N/A')}")
            print(f"    Account: {aws_instance.get('aws_account_id', 'N/A')}")
            print(f"    Region: {aws_instance.get('aws_region', 'N/A')}")
            print(f"    AZ: {aws_instance.get('aws_availability_zone', 'N/A')}")
            print(f"    VPC: {aws_instance.get('aws_vpc_id', 'N/A')}")
            print(f"    Subnet: {aws_instance.get('aws_subnet_id', 'N/A')}")
            print(f"    Security Groups: {aws_instance.get('aws_security_groups', 'N/A')}")
            print(f"    Tags: {aws_instance.get('aws_tags', 'N/A')}")
            print("")
    else:
        print("No AWS instances found for application")
    print("")
except Exception as e:
    print(f"Error querying AWS instances: {str(e)}")

# Query tags and attributes
print("=== Server Tags and Attributes ===")
tag_params = {
    'sysparm_query': f'application={app_sys_id}',
    'sysparm_fields': 'sys_id,name,host_name,tags,attributes',
    'sysparm_limit': 100
}

try:
    tag_results = make_request('table/cmdb_ci_server', tag_params)
    if tag_results.get('result'):
        print(f"Server tags and attributes:")
        for server in tag_results['result']:
            server_name = server.get('name', 'N/A')
            tags = server.get('tags', 'N/A')
            attributes = server.get('attributes', 'N/A')
            print(f"  {server_name}:")
            print(f"    Tags: {tags}")
            print(f"    Attributes: {attributes}")
            print("")
    else:
        print("No tag information available")
    print("")
except Exception as e:
    print(f"Error querying tags: {str(e)}")

print("=== CMDB Query Complete ===")
