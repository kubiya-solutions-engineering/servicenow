from typing import List
import sys
from servicenow_tools.tools.base import ServiceNowTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CMDBQueryTool(ServiceNowTool):
    """Tool to query ServiceNow CMDB for servers linked to applications."""
    
    def __init__(self):
        super().__init__(
            name="servicenow_cmdb_query",
            description="Query ServiceNow CMDB for all servers linked to a chosen application, collecting server names/IDs, tags, and AWS account/region data",
            content="""
# CMDB Query Tool
application_id = os.getenv('application_id', '')

if not application_id:
    print("Error: application_id parameter is required")
    sys.exit(1)

print(f"Querying CMDB for servers linked to application: {application_id}")
print("")

# First, get the application details
print("=== Application Details ===")
app_params = {
    'sysparm_query': f'sys_id={application_id}^ORnameLIKE{application_id}',
    'sysparm_fields': 'sys_id,name,short_description,state,operational_status,owner',
    'sysparm_limit': 1
}

try:
    app_results = make_request('table/apm_application', app_params)
    if not app_results.get('result'):
        print(f"Application not found: {application_id}")
        sys.exit(1)
    
    app = app_results['result'][0]
    app_sys_id = app.get('sys_id')
    print(f"Application: {app.get('name', 'N/A')} (ID: {app_sys_id})")
    print(f"Description: {app.get('short_description', 'N/A')}")
    print(f"State: {app.get('state', 'N/A')}, Status: {app.get('operational_status', 'N/A')}")
    print(f"Owner: {app.get('owner', 'N/A')}")
    print("")
    
except Exception as e:
    print(f"Error finding application: {str(e)}")
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
""",
            args=[
                Arg(
                    name="application_id", 
                    description="Application sys_id or name to query servers for", 
                    required=True
                )
            ]
        )

# Self-register the tool
try:
    tool = CMDBQueryTool()
    tool_registry.register("servicenow", tool)
    print(f"✅ Registered: {tool.name}")
except Exception as e:
    print(f"❌ Failed to register CMDB Query tool: {str(e)}", file=sys.stderr)
    raise
