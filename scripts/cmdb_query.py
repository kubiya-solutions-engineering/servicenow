#!/usr/bin/env python3
import requests
import json
import os
import sys

# ServiceNow configuration
SN_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
SN_USERNAME = os.getenv('SERVICENOW_USERNAME')
SN_PASSWORD = os.getenv('SERVICENOW_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    error_response = {"error": "Missing required ServiceNow environment variables", "required": ["SERVICENOW_INSTANCE", "SERVICENOW_USERNAME", "SERVICENOW_PASSWORD"]}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)

# Common headers for API requests
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Authentication
AUTH = (SN_USERNAME, SN_PASSWORD)

def make_request(table_name, params=None, method='GET'):
    """Make authenticated request to ServiceNow API"""
    # Handle both cases: instance name only or full URL
    if SN_INSTANCE.startswith('http'):
        base_url = SN_INSTANCE
    else:
        base_url = f"https://{SN_INSTANCE}.service-now.com"
    
    url = f"{base_url}/api/now/table/{table_name}"
    
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
        error_response = {"error": f"ServiceNow API request failed", "url": url, "details": str(e)}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)

# CMDB Query Tool
import argparse

parser = argparse.ArgumentParser(description='Query ServiceNow CMDB for servers')
parser.add_argument('application_id', help='Application sys_id or name to query servers for')
args = parser.parse_args()

application_id = args.application_id

# First, find the application in cmdb_ci_appl
app_params = {
    'sysparm_query': f'sys_id={application_id}^ORnameLIKE{application_id}',
    'sysparm_fields': 'sys_id,name,short_description,operational_status,assigned_to,owned_by',
    'sysparm_limit': 10
}

try:
    app_results = make_request('cmdb_ci_appl', app_params)
    
    if not app_results.get('result'):
        error_response = {"error": "Application not found", "searched": application_id}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)
    
    # Handle multiple matches
    apps = app_results['result']
    if len(apps) > 1:
        error_response = {"error": "Multiple applications found", "searched": application_id, "count": len(apps)}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)
    
    app = apps[0]
    app_sys_id = app.get('sys_id')
    
    # Query servers linked to this application through relationships
    relationship_params = {
        'sysparm_query': f'parent={app_sys_id}^type=Used by^ORparent={app_sys_id}^type=Uses^ORparent={app_sys_id}^type=Hosted on^ORparent={app_sys_id}^type=Hosts^ORparent={app_sys_id}^type=Runs on',
        'sysparm_fields': 'sys_id,parent,child,type',
        'sysparm_limit': 100
    }
    
    relationship_results = make_request('cmdb_rel_ci', relationship_params)
    servers = []
    
    if relationship_results.get('result'):
        # Collect all related CI IDs
        related_ci_ids = [rel.get('child') for rel in relationship_results['result'] if rel.get('child')]
        
        if related_ci_ids:
            # Query servers from the related CIs
            server_query = '^OR'.join([f'sys_id={ci_id}' for ci_id in related_ci_ids])
            server_params = {
                'sysparm_query': f'class_name=cmdb_ci_server^{server_query}',
                'sysparm_fields': 'sys_id,name,host_name,ip_address,operational_status,os_name,os_version,cpu_count,ram,disk_space,location,assigned_to,owned_by,serial_number,asset_tag,u_aws_account,u_aws_region,u_aws_instance_id',
                'sysparm_limit': 100
            }
            
            server_results = make_request('cmdb_ci', server_params)
            if server_results.get('result'):
                for server in server_results['result']:
                    server_info = {
                        "sys_id": server.get('sys_id'),
                        "name": server.get('name'),
                        "host_name": server.get('host_name'),
                        "ip_address": server.get('ip_address'),
                        "operational_status": server.get('operational_status'),
                        "os_name": server.get('os_name'),
                        "os_version": server.get('os_version'),
                        "cpu_count": server.get('cpu_count'),
                        "ram": server.get('ram'),
                        "disk_space": server.get('disk_space'),
                        "location": server.get('location'),
                        "assigned_to": server.get('assigned_to'),
                        "owned_by": server.get('owned_by'),
                        "serial_number": server.get('serial_number'),
                        "asset_tag": server.get('asset_tag'),
                        "aws_account": server.get('u_aws_account'),
                        "aws_region": server.get('u_aws_region'),
                        "aws_instance_id": server.get('u_aws_instance_id')
                    }
                    servers.append(server_info)
    
    # Format response
    response = {
        "application_id": application_id,
        "application": {
            "sys_id": app.get('sys_id'),
            "name": app.get('name'),
            "description": app.get('short_description'),
            "operational_status": app.get('operational_status'),
            "assigned_to": app.get('assigned_to'),
            "owned_by": app.get('owned_by')
        },
        "servers_found": len(servers),
        "servers": servers
    }
    
    print(json.dumps(response, indent=2))
    
except Exception as e:
    error_response = {"error": f"Failed to query CMDB", "searched": application_id, "details": str(e)}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)