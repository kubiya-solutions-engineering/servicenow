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

# APM Catalog Query Tool
import argparse

parser = argparse.ArgumentParser(description='Query ServiceNow APM catalog')
parser.add_argument('search_term', help='Term to search for in APM catalog')
args = parser.parse_args()

search_term = args.search_term

# Query CMDB Application table (since APM is not available)
app_params = {
    'sysparm_query': f'nameLIKE{search_term}^ORshort_descriptionLIKE{search_term}^ORsys_id={search_term}',
    'sysparm_fields': 'sys_id,name,short_description,operational_status,assigned_to,owned_by,category,subcategory',
    'sysparm_limit': 50
}

try:
    app_results = make_request('cmdb_ci_appl', app_params)
    
    if not app_results.get('result'):
        error_response = {"error": "Application not found", "searched": search_term}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)
    
    # Format results as structured JSON
    applications = []
    for app in app_results['result']:
        application = {
            "sys_id": app.get('sys_id'),
            "name": app.get('name'),
            "description": app.get('short_description'),
            "operational_status": app.get('operational_status'),
            "assigned_to": app.get('assigned_to'),
            "owned_by": app.get('owned_by'),
            "category": app.get('category'),
            "subcategory": app.get('subcategory')
        }
        applications.append(application)
    
    response = {
        "search_term": search_term,
        "applications_found": len(applications),
        "applications": applications
    }
    
    print(json.dumps(response, indent=2))
    
except Exception as e:
    error_response = {"error": f"Failed to query applications", "searched": search_term, "details": str(e)}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)