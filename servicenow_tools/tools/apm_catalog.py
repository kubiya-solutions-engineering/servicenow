import inspect
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kubiya_sdk.tools.models import Arg, FileSpec, Volume
from kubiya_sdk.tools.registry import tool_registry

from .base import ServiceNowTool

# Read the APM catalog script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "apm_catalog.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
apm_catalog_tool = ServiceNowTool(
    name="servicenow_apm_catalog_query",
    description="Query ServiceNow APM catalog to match applications/services by name or identifier",
    content="""
    set -e
    python -m venv /opt/venv > /dev/null
    . /opt/venv/bin/activate > /dev/null
    pip install requests==2.32.3 2>&1 | grep -v '[notice]'

            # Run the APM catalog script
            python /opt/scripts/apm_catalog.py "{{ .search_term }}"
    """,
    args=[
        Arg(
            name="search_term",
            description="Term to search for in APM catalog (application name, service name, or sys_id)",
            required=True,
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/apm_catalog.py",
            content=script_content,
        ),
    ],
    long_running=False,
    mermaid="""
    sequenceDiagram
        participant A as Agent
        participant S as ServiceNow
        participant APM as APM Catalog

        A ->> S: Query APM Catalog
        S ->> APM: Search Applications
        S ->> APM: Search Services
        S ->> APM: Search Components
        APM -->> S: Return Results
        S -->> A: Application Data
    """,
)

# Register the tool
tool_registry.register("servicenow", apm_catalog_tool)