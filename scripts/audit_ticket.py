#!/usr/bin/env python3
import requests
import json
import os
import sys
from datetime import datetime

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

# Build base URL for ServiceNow instance
if SN_INSTANCE.startswith('http'):
    BASE_URL = SN_INSTANCE
else:
    BASE_URL = f"https://{SN_INSTANCE}.service-now.com"

def make_request(table_name, params=None, method='GET'):
    """Make authenticated request to ServiceNow API"""
    url = f"{BASE_URL}/api/now/table/{table_name}"
    
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

# Audit Ticket Tool
import argparse

parser = argparse.ArgumentParser(description='Create ServiceNow audit ticket for server operations')
parser.add_argument('--user', required=True, help='User who initiated the action (email or username)')
parser.add_argument('--action', required=True, help='Action performed (e.g., "server_startup", "server_shutdown", "application_deployment")')
parser.add_argument('--application', required=True, help='Application name or identifier')
parser.add_argument('--servers', required=True, help='Comma-separated list of server names/IDs affected')
parser.add_argument('--status', required=True, help='Operation status (success, failure, partial)')
parser.add_argument('--details', help='Additional details about the operation')
parser.add_argument('--teams_channel', help='Teams channel where request originated')
parser.add_argument('--aws_account', help='AWS account ID where servers are located')
parser.add_argument('--aws_region', help='AWS region where servers are located')
args = parser.parse_args()

# Get current timestamp
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

# Build the ticket description
description_parts = [
    f"**AUDIT TRAIL - Server Operation**",
    f"",
    f"**WHO:** {args.user}",
    f"**WHAT:** {args.action}",
    f"**WHEN:** {current_time}",
    f"**APPLICATION:** {args.application}",
    f"**SERVERS:** {args.servers}",
    f"**STATUS:** {args.status.upper()}",
    f""
]

if args.teams_channel:
    description_parts.append(f"**TEAMS CHANNEL:** {args.teams_channel}")

if args.aws_account:
    description_parts.append(f"**AWS ACCOUNT:** {args.aws_account}")

if args.aws_region:
    description_parts.append(f"**AWS REGION:** {args.aws_region}")

if args.details:
    description_parts.extend([
        f"",
        f"**DETAILS:**",
        f"{args.details}"
    ])

description_parts.extend([
    f"",
    f"**AUDIT INFORMATION:**",
    f"- This ticket was automatically created by Kubiya automation",
    f"- Operation initiated via Microsoft Teams chat",
    f"- All actions logged for compliance and audit purposes"
])

ticket_description = "\n".join(description_parts)

# Create the incident ticket
ticket_data = {
    "short_description": f"Audit: {args.action} for {args.application} - {args.status.upper()}",
    "description": ticket_description,
    "category": "Infrastructure",
    "subcategory": "Server Management",
    "priority": "3",  # Medium priority
    "urgency": "3",   # Medium urgency
    "state": "1",     # New
    "caller_id": args.user,
    "assigned_to": "",  # Leave unassigned for now
    "work_notes": f"Automated audit ticket created at {current_time} for {args.action} operation on {args.application}",
    "comments": f"Operation Status: {args.status.upper()}\nServers Affected: {args.servers}\nInitiated by: {args.user}",
    "u_audit_type": "Server Operation",
    "u_operation_type": args.action,
    "u_application_name": args.application,
    "u_servers_affected": args.servers,
    "u_operation_status": args.status,
    "u_teams_channel": args.teams_channel or "",
    "u_aws_account": args.aws_account or "",
    "u_aws_region": args.aws_region or ""
}

try:
    # Create the incident
    incident_result = make_request('incident', ticket_data, method='POST')
    
    if incident_result.get('result'):
        incident = incident_result['result']
        incident_number = incident.get('number')
        incident_sys_id = incident.get('sys_id')
        
        # Also create a change request for tracking purposes
        change_data = {
            "short_description": f"Change: {args.action} for {args.application}",
            "description": f"Change request created for audit trail of {args.action} operation on {args.application}",
            "category": "Infrastructure",
            "subcategory": "Server Management",
            "priority": "3",
            "risk": "Low",
            "type": "Standard",
            "state": "1",  # New
            "requested_by": args.user,
            "assigned_to": "",
            "work_notes": f"Related to incident {incident_number}",
            "u_related_incident": incident_sys_id,
            "u_operation_type": args.action,
            "u_application_name": args.application
        }
        
        change_result = make_request('change_request', change_data, method='POST')
        
        response = {
            "success": True,
            "message": "Audit ticket created successfully",
            "incident": {
                "number": incident_number,
                "sys_id": incident_sys_id,
                "url": f"{BASE_URL}/incident.do?sys_id={incident_sys_id}"
            },
            "change_request": {
                "number": change_result['result'].get('number') if change_result.get('result') else None,
                "sys_id": change_result['result'].get('sys_id') if change_result.get('result') else None
            },
            "audit_details": {
                "user": args.user,
                "action": args.action,
                "application": args.application,
                "servers": args.servers,
                "status": args.status,
                "timestamp": current_time,
                "teams_channel": args.teams_channel,
                "aws_account": args.aws_account,
                "aws_region": args.aws_region
            }
        }
        
        print(json.dumps(response, indent=2))
    else:
        error_response = {"error": "Failed to create incident ticket", "details": "No result returned from ServiceNow API"}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)
        
except Exception as e:
    error_response = {"error": f"Failed to create audit ticket", "details": str(e)}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)
