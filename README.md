# ServiceNow Tools

This module provides integration tools for ServiceNow, allowing you to interact with various ServiceNow APIs and data sources.

## Available Tools

### 1. APM Catalog Query (`servicenow_apm_catalog_query`)

Queries the ServiceNow APM (Application Portfolio Management) catalog to find applications, services, and components that match a given search term.

**Parameters:**
- `search_term` (required): Term to search for in APM catalog (application name, service name, or sys_id)

**Features:**
- Searches across APM Applications, Services, and Components
- Returns detailed information including names, descriptions, states, and ownership
- Supports partial matching and sys_id lookups

### 2. Identity Check (`servicenow_identity_check`)

Checks a user's identity against ServiceNow roles, group memberships, entitlements, and access control rules.

**Parameters:**
- `user_identifier` (required): User identifier to check (email address, username, or sys_id)

**Features:**
- Finds user records by email, username, or sys_id
- Lists all assigned roles and their descriptions
- Shows group memberships
- Displays entitlements and expiration dates
- Reports access control rules

### 3. CMDB Query (`servicenow_cmdb_query`)

Queries the ServiceNow CMDB (Configuration Management Database) for all servers linked to a chosen application, collecting comprehensive server information.

**Parameters:**
- `application_id` (required): Application sys_id or name to query servers for

**Features:**
- Finds servers directly linked to applications
- Discovers servers through service relationships
- Collects server details (hostname, IP, OS, hardware specs)
- Retrieves AWS-specific information (account, region, instance details)
- Gathers tags and custom attributes

### 4. Audit Ticket (`servicenow_audit_ticket`)

Creates ServiceNow audit tickets to track "who, what, when" for server operations and maintain compliance audit trails.

**Parameters:**
- `user` (required): User who initiated the action (email address or username)
- `action` (required): Action performed (e.g., "server_startup", "server_shutdown", "application_deployment")
- `application` (required): Application name or identifier that was affected
- `servers` (required): Comma-separated list of server names/IDs that were affected
- `status` (required): Operation status ("success", "failure", or "partial")
- `details` (optional): Additional details about the operation
- `teams_channel` (optional): Microsoft Teams channel where request originated
- `aws_account` (optional): AWS account ID where servers are located
- `aws_region` (optional): AWS region where servers are located

**Features:**
- Creates both incident and change request tickets for comprehensive audit trail
- Tracks who initiated the action, what was done, and when it occurred
- Includes detailed operation information (servers, status, AWS details)
- Links Teams channel information for traceability
- Provides direct URLs to created tickets
- Supports compliance and audit requirements

## Configuration

### Environment Variables

All tools require the following environment variables:

- `SERVICENOW_INSTANCE`: Your ServiceNow instance name (e.g., "mycompany")
- `SERVICENOW_USERNAME`: ServiceNow username for API authentication
- `SERVICENOW_PASSWORD`: ServiceNow password for API authentication

### Authentication

The tools use basic authentication with your ServiceNow credentials and the standard ServiceNow REST API endpoint format (`api/now/table`). Make sure the user account has appropriate permissions to access the required tables:

- `apm_application`
- `apm_service`
- `apm_component`
- `sys_user`
- `sys_user_has_role`
- `sys_user_grmember`
- `sys_user_entitlement`
- `sys_security_acl`
- `cmdb_ci_server`
- `cmdb_ci_aws_instance`
- `cmdb_ci` (for general CMDB queries)
- `cmdb_rel_ci` (for CMDB relationships)
- `incident` (for creating audit incident tickets)
- `change_request` (for creating audit change request tickets)

## Usage Examples

### Query APM Catalog
```python
# Search for applications containing "web"
tool = APMCatalogTool()
result = tool.execute({"search_term": "web"})
```

### Check User Identity
```python
# Check user by email
tool = IdentityCheckTool()
result = tool.execute({"user_identifier": "john.doe@company.com"})
```

### Query CMDB for Application Servers
```python
# Find all servers for an application
tool = CMDBQueryTool()
result = tool.execute({"application_id": "web-application-001"})
```

### Create Audit Ticket
```python
# Create audit ticket for server startup operation
tool = AuditTicketTool()
result = tool.execute({
    "user": "john.doe@company.com",
    "action": "server_startup",
    "application": "web-application-001",
    "servers": "web-server-01,web-server-02,web-server-03",
    "status": "success",
    "details": "All servers started successfully for production deployment",
    "teams_channel": "devops-alerts",
    "aws_account": "123456789012",
    "aws_region": "us-east-1"
})
```

## Architecture

The ServiceNow tools follow the same pattern as the AWS tools:

- **Base Class**: `ServiceNowTool` provides common functionality for API authentication and request handling
- **Individual Tools**: Each tool inherits from the base class and implements specific ServiceNow API interactions
- **Registry**: All tools are automatically registered when the module is imported

## Error Handling

All tools include comprehensive error handling:
- Validates required environment variables
- Checks API response status codes
- Provides detailed error messages for troubleshooting
- Gracefully handles missing data or API failures

## Dependencies

- `requests`: For HTTP API calls to ServiceNow
- `kubiya_sdk`: For tool framework integration
- Python 3.11+ (Docker image: `python:3.11-slim`)
