from typing import List
import sys
from .base import ServiceNowTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class APMCatalogTool(ServiceNowTool):
    """Tool to query ServiceNow APM catalog for applications and services."""
    
    def __init__(self):
        super().__init__(
            name="servicenow_apm_catalog_query",
            description="Query ServiceNow APM catalog to match applications/services by name or identifier",
            content="""
# APM Catalog Query Tool
search_term = os.getenv('search_term', '')

if not search_term:
    print("Error: search_term parameter is required")
    sys.exit(1)

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
    app_results = make_request('table/apm_application', app_params)
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
""",
            args=[
                Arg(
                    name="search_term", 
                    description="Term to search for in APM catalog (application name, service name, or sys_id)", 
                    required=True
                )
            ]
        )

# Self-register the tool
try:
    tool = APMCatalogTool()
    tool_registry.register("servicenow", tool)
    print(f"✅ Registered: {tool.name}")
except Exception as e:
    print(f"❌ Failed to register APM Catalog tool: {str(e)}", file=sys.stderr)
    raise
