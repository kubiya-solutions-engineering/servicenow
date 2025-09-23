from typing import List
import sys
from .base import ServiceNowTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class IdentityCheckTool(ServiceNowTool):
    """Tool to check user identity against ServiceNow roles and entitlements."""
    
    def __init__(self):
        super().__init__(
            name="servicenow_identity_check",
            description="Check user's identity (via email or Teams) against ServiceNow roles and entitlement tables",
            content="""
# Identity Check Tool
user_identifier = os.getenv('user_identifier', '')

if not user_identifier:
    print("Error: user_identifier parameter is required")
    sys.exit(1)

print(f"Checking identity for: {user_identifier}")
print("")

# Query User table to find the user
print("=== Finding User Record ===")
user_params = {
    'sysparm_query': f'email={user_identifier}^ORuser_name={user_identifier}^ORsys_id={user_identifier}',
    'sysparm_fields': 'sys_id,user_name,first_name,last_name,email,active,locked_out,last_login_time',
    'sysparm_limit': 10
}

try:
    user_results = make_request('table/sys_user', user_params)
    if not user_results.get('result'):
        print(f"No user found with identifier: {user_identifier}")
        sys.exit(1)
    
    user = user_results['result'][0]  # Take first match
    user_sys_id = user.get('sys_id')
    print(f"Found user: {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('user_name', 'N/A')})")
    print(f"Email: {user.get('email', 'N/A')}")
    print(f"Active: {user.get('active', 'N/A')}, Locked: {user.get('locked_out', 'N/A')}")
    print(f"Last Login: {user.get('last_login_time', 'N/A')}")
    print("")
    
except Exception as e:
    print(f"Error finding user: {str(e)}")
    sys.exit(1)

# Query User Roles
print("=== User Roles ===")
role_params = {
    'sysparm_query': f'user={user_sys_id}',
    'sysparm_fields': 'sys_id,user,role,name,description,active',
    'sysparm_limit': 100
}

try:
    role_results = make_request('table/sys_user_has_role', role_params)
    if role_results.get('result'):
        print(f"User has {len(role_results['result'])} roles:")
        for role_assignment in role_results['result']:
            role_name = role_assignment.get('name', 'N/A')
            role_desc = role_assignment.get('description', 'N/A')
            active = role_assignment.get('active', 'N/A')
            print(f"  - {role_name}: {role_desc} (Active: {active})")
    else:
        print("No roles assigned to user")
    print("")
except Exception as e:
    print(f"Error querying user roles: {str(e)}")

# Query Group Memberships
print("=== Group Memberships ===")
group_params = {
    'sysparm_query': f'user={user_sys_id}',
    'sysparm_fields': 'sys_id,user,group,name,description,active',
    'sysparm_limit': 100
}

try:
    group_results = make_request('table/sys_user_grmember', group_params)
    if group_results.get('result'):
        print(f"User is member of {len(group_results['result'])} groups:")
        for group_membership in group_results['result']:
            group_name = group_membership.get('name', 'N/A')
            group_desc = group_membership.get('description', 'N/A')
            active = group_membership.get('active', 'N/A')
            print(f"  - {group_name}: {group_desc} (Active: {active})")
    else:
        print("User is not a member of any groups")
    print("")
except Exception as e:
    print(f"Error querying group memberships: {str(e)}")

# Query Entitlements (if available)
print("=== Entitlements ===")
entitlement_params = {
    'sysparm_query': f'user={user_sys_id}',
    'sysparm_fields': 'sys_id,user,entitlement,name,description,active,expires',
    'sysparm_limit': 100
}

try:
    entitlement_results = make_request('table/sys_user_entitlement', entitlement_params)
    if entitlement_results.get('result'):
        print(f"User has {len(entitlement_results['result'])} entitlements:")
        for entitlement in entitlement_results['result']:
            ent_name = entitlement.get('name', 'N/A')
            ent_desc = entitlement.get('description', 'N/A')
            active = entitlement.get('active', 'N/A')
            expires = entitlement.get('expires', 'N/A')
            print(f"  - {ent_name}: {ent_desc} (Active: {active}, Expires: {expires})")
    else:
        print("No entitlements found for user")
    print("")
except Exception as e:
    print(f"Error querying entitlements: {str(e)}")

# Query Access Control Rules (if available)
print("=== Access Control Rules ===")
acr_params = {
    'sysparm_query': f'user={user_sys_id}',
    'sysparm_fields': 'sys_id,user,role,table,operation,condition,active',
    'sysparm_limit': 100
}

try:
    acr_results = make_request('table/sys_security_acl', acr_params)
    if acr_results.get('result'):
        print(f"User has {len(acr_results['result'])} access control rules:")
        for acr in acr_results['result']:
            role = acr.get('role', 'N/A')
            table = acr.get('table', 'N/A')
            operation = acr.get('operation', 'N/A')
            condition = acr.get('condition', 'N/A')
            active = acr.get('active', 'N/A')
            print(f"  - Role: {role}, Table: {table}, Operation: {operation}")
            print(f"    Condition: {condition} (Active: {active})")
    else:
        print("No specific access control rules found for user")
    print("")
except Exception as e:
    print(f"Error querying access control rules: {str(e)}")

print("=== Identity Check Complete ===")
""",
            args=[
                Arg(
                    name="user_identifier", 
                    description="User identifier to check (email address, username, or sys_id)", 
                    required=True
                )
            ]
        )

# Self-register the tool
try:
    tool = IdentityCheckTool()
    tool_registry.register("servicenow", tool)
    print(f"✅ Registered: {tool.name}")
except Exception as e:
    print(f"❌ Failed to register Identity Check tool: {str(e)}", file=sys.stderr)
    raise
