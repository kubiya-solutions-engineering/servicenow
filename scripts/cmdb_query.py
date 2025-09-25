#!/usr/bin/env python3
import requests
import json
import os
import sys
import argparse

# ServiceNow configuration
SN_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
SN_USERNAME = os.getenv('SERVICENOW_USERNAME')
SN_PASSWORD = os.getenv('SERVICENOW_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    error_response = {
        "error": "Missing required ServiceNow environment variables",
        "required": ["SERVICENOW_INSTANCE", "SERVICENOW_USERNAME", "SERVICENOW_PASSWORD"]
    }
    print(json.dumps(error_response, indent=2))
    sys.exit(1)

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
AUTH = (SN_USERNAME, SN_PASSWORD)

def make_request(table_name, params=None, method='GET'):
    """Make authenticated request to ServiceNow API"""
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
        error_response = {
            "error": "ServiceNow API request failed",
            "url": url,
            "details": str(e)
        }
        print(json.dumps(error_response, indent=2))
        sys.exit(1)

# CLI args
parser = argparse.ArgumentParser(description='Query ServiceNow CMDB for servers')
parser.add_argument('application_id', help='Application sys_id or name to query servers for')
args = parser.parse_args()
application_id = args.application_id

# Query cmdb_ci_appl
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

    apps = app_results['result']
    if len(apps) > 1:
        error_response = {"error": "Multiple applications found", "searched": application_id, "count": len(apps)}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)

    app = apps[0]
    app_sys_id = app.get('sys_id')
    servers = []

    # --- Try relationships first ---
    rel_params = {
        'sysparm_query': f'parent={app_sys_id}',
        'sysparm_fields': 'sys_id,parent,child,type',
        'sysparm_limit': 100
    }
    rel_results = make_request('cmdb_rel_ci', rel_params)

    if rel_results.get('result'):
        child_ids = [rel['child']['value'] for rel in rel_results['result'] if rel.get('child')]
        if child_ids:
            query = '^OR'.join([f'sys_id={cid}' for cid in child_ids])
            server_params = {
                'sysparm_query': query,
                'sysparm_fields': 'sys_id,name,host_name,ip_address,operational_status,os,u_aws_account,u_aws_region,u_aws_instance_id',
                'sysparm_limit': 100
            }
            server_results = make_request('cmdb_ci_server', server_params)
            if server_results.get('result'):
                servers.extend(server_results['result'])

    # --- Fallback: direct u_application reference ---
    if not servers:
        direct_params = {
            'sysparm_query': f'u_application={app_sys_id}',
            'sysparm_fields': 'sys_id,name,host_name,ip_address,operational_status,os,u_aws_account,u_aws_region,u_aws_instance_id',
            'sysparm_limit': 100
        }
        direct_results = make_request('cmdb_ci_server', direct_params)
        if direct_results.get('result'):
            servers.extend(direct_results['result'])

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
    error_response = {
        "error": "Failed to query CMDB",
        "searched": application_id,
        "details": str(e)
    }
    print(json.dumps(error_response, indent=2))
    sys.exit(1)
