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

# Identity Check Tool
import argparse

parser = argparse.ArgumentParser(description='Check user identity in ServiceNow')
parser.add_argument('user_identifier', help='User identifier to check (email, username, or sys_id)')
args = parser.parse_args()

user_identifier = args.user_identifier

# Query User table to find the user
user_params = {
    'sysparm_query': f'email={user_identifier}^ORuser_name={user_identifier}^ORsys_id={user_identifier}',
    'sysparm_fields': 'sys_id,user_name,first_name,last_name,email,active,locked_out,last_login_time,department,location',
    'sysparm_limit': 10
}

try:
    user_results = make_request('sys_user', user_params)
    
    if not user_results.get('result'):
        error_response = {"error": "User not found", "searched": user_identifier}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)
    
    # Handle multiple matches
    users = user_results['result']
    if len(users) > 1:
        error_response = {"error": "Multiple users found", "searched": user_identifier, "count": len(users)}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)
    
    user = users[0]
    user_sys_id = user.get('sys_id')
    
    # Query user roles
    role_params = {
        'sysparm_query': f'user={user_sys_id}',
        'sysparm_fields': 'user,role',
        'sysparm_limit': 100
    }
    
    role_results = make_request('sys_user_has_role', role_params)
    roles = []
    
    if role_results.get('result'):
        # Get role names for each role sys_id
        for user_role in role_results['result']:
            role_sys_id = user_role.get('role')
            if role_sys_id:
                # Query sys_user_role table to get role name
                role_name_params = {
                    'sysparm_query': f'sys_id={role_sys_id}',
                    'sysparm_fields': 'sys_id,name,description',
                    'sysparm_limit': 1
                }
                
                role_name_results = make_request('sys_user_role', role_name_params)
                if role_name_results.get('result'):
                    role_info = role_name_results['result'][0]
                    roles.append({
                        "sys_id": role_info.get('sys_id'),
                        "name": role_info.get('name'),
                        "description": role_info.get('description')
                    })
    
    # Query group memberships
    group_params = {
        'sysparm_query': f'user={user_sys_id}',
        'sysparm_fields': 'user,group',
        'sysparm_limit': 100
    }
    
    group_results = make_request('sys_user_grmember', group_params)
    groups = []
    
    if group_results.get('result'):
        # Get group names for each group sys_id
        for user_group in group_results['result']:
            group_sys_id = user_group.get('group')
            if group_sys_id:
                # Query sys_user_group table to get group name
                group_name_params = {
                    'sysparm_query': f'sys_id={group_sys_id}',
                    'sysparm_fields': 'sys_id,name,description',
                    'sysparm_limit': 1
                }
                
                group_name_results = make_request('sys_user_group', group_name_params)
                if group_name_results.get('result'):
                    group_info = group_name_results['result'][0]
                    groups.append({
                        "sys_id": group_info.get('sys_id'),
                        "name": group_info.get('name'),
                        "description": group_info.get('description')
                    })
    
    # Format response
    response = {
        "user_identifier": user_identifier,
        "user": {
            "sys_id": user.get('sys_id'),
            "user_name": user.get('user_name'),
            "first_name": user.get('first_name'),
            "last_name": user.get('last_name'),
            "email": user.get('email'),
            "active": user.get('active'),
            "locked_out": user.get('locked_out'),
            "last_login_time": user.get('last_login_time'),
            "department": user.get('department'),
            "location": user.get('location')
        },
        "roles": roles,
        "groups": groups,
        "role_count": len(roles),
        "group_count": len(groups)
    }
    
    print(json.dumps(response, indent=2))
    
except Exception as e:
    error_response = {"error": f"Failed to check user identity", "searched": user_identifier, "details": str(e)}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)