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
