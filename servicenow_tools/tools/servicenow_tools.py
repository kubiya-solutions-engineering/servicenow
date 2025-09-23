from typing import List
import sys
from .base import ServiceNowTool, Arg
from .apm_catalog import APMCatalogTool
from .identity_check import IdentityCheckTool
from .cmdb_query import CMDBQueryTool
from kubiya_sdk.tools.registry import tool_registry

class ServiceNowTools:
    """ServiceNow integration tools."""

    def __init__(self):
        """Initialize and register all ServiceNow tools."""
        try:
            tools = [
                self.apm_catalog_query(),
                self.identity_check(),
                self.cmdb_query()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("servicenow", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ServiceNow tools: {str(e)}", file=sys.stderr)
            raise

    def apm_catalog_query(self) -> APMCatalogTool:
        """Query ServiceNow APM catalog for applications and services."""
        return APMCatalogTool()

    def identity_check(self) -> IdentityCheckTool:
        """Check user identity against ServiceNow roles and entitlements."""
        return IdentityCheckTool()

    def cmdb_query(self) -> CMDBQueryTool:
        """Query ServiceNow CMDB for servers linked to applications."""
        return CMDBQueryTool()

ServiceNowTools()
