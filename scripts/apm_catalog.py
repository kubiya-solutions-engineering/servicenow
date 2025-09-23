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

# APM Catalog Query Tool
import argparse

parser = argparse.ArgumentParser(description='Query ServiceNow APM catalog')
parser.add_argument('search_term', help='Term to search for in APM catalog')
args = parser.parse_args()

search_term = args.search_term

print(f"Searching APM catalog for: {search_term}")
print("")

# Query APM Application table
print("=== Searching APM Applications ===")
app_params = {
    'sysparm_query': f'nameLIKE{search_term}^ORshort_descriptionLIKE{search_term}^ORsys_id={search_term}',
    'sysparm_fields': 'sys_id,name,short_description,state,operational_status,owner,assigned_to',
    'sysparm_limit': 50
}

try:
    app_results = make_request('table/sn_apm_cm_application', app_params)
    if app_results.get('result'):
        print(f"Found {len(app_results['result'])} applications:")
        for app in app_results['result']:
            print(f"  - {app.get('name', 'N/A')} (ID: {app.get('sys_id', 'N/A')})")
            print(f"    Description: {app.get('short_description', 'N/A')}")
            print(f"    State: {app.get('state', 'N/A')}, Status: {app.get('operational_status', 'N/A')}")
            print(f"    Owner: {app.get('owner', 'N/A')}")
            print("")
    else:
        print("No applications found")
except Exception as e:
    print(f"Error querying applications: {str(e)}")

# Query APM Service table
print("=== Searching APM Services ===")
service_params = {
    'sysparm_query': f'nameLIKE{search_term}^ORshort_descriptionLIKE{search_term}^ORsys_id={search_term}',
    'sysparm_fields': 'sys_id,name,short_description,state,operational_status,owner,assigned_to,application',
    'sysparm_limit': 50
}

try:
    service_results = make_request('table/apm_service', service_params)
    if service_results.get('result'):
        print(f"Found {len(service_results['result'])} services:")
        for service in service_results['result']:
            print(f"  - {service.get('name', 'N/A')} (ID: {service.get('sys_id', 'N/A')})")
            print(f"    Description: {service.get('short_description', 'N/A')}")
            print(f"    State: {service.get('state', 'N/A')}, Status: {service.get('operational_status', 'N/A')}")
            print(f"    Owner: {service.get('owner', 'N/A')}")
            print(f"    Application: {service.get('application', 'N/A')}")
            print("")
    else:
        print("No services found")
except Exception as e:
    print(f"Error querying services: {str(e)}")

# Query APM Component table
print("=== Searching APM Components ===")
component_params = {
    'sysparm_query': f'nameLIKE{search_term}^ORshort_descriptionLIKE{search_term}^ORsys_id={search_term}',
    'sysparm_fields': 'sys_id,name,short_description,state,operational_status,owner,assigned_to,application,service',
    'sysparm_limit': 50
}

try:
    component_results = make_request('table/apm_component', component_params)
    if component_results.get('result'):
        print(f"Found {len(component_results['result'])} components:")
        for component in component_results['result']:
            print(f"  - {component.get('name', 'N/A')} (ID: {component.get('sys_id', 'N/A')})")
            print(f"    Description: {component.get('short_description', 'N/A')}")
            print(f"    State: {component.get('state', 'N/A')}, Status: {component.get('operational_status', 'N/A')}")
            print(f"    Owner: {component.get('owner', 'N/A')}")
            print(f"    Application: {component.get('application', 'N/A')}")
            print(f"    Service: {component.get('service', 'N/A')}")
            print("")
    else:
        print("No components found")
except Exception as e:
    print(f"Error querying components: {str(e)}")

print("=== APM Catalog Search Complete ===")
