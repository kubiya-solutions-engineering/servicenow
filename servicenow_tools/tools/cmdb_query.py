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

# Read the CMDB query script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "cmdb_query.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
cmdb_query_tool = ServiceNowTool(
    name="servicenow_cmdb_query",
    description="Query ServiceNow CMDB for all servers linked to a chosen application, collecting server names/IDs, tags, and AWS account/region data",
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install requests==2.32.3 2>&1 | grep -v '[notice]'

# Run the CMDB query script
python /opt/scripts/cmdb_query.py "{{ .application_id }}"
""",
    args=[
        Arg(
            name="application_id",
            description="Application identifier - can be application name (e.g., 'XYZ', 'MyApp') or exact sys_id (e.g., 'abc123def456'). The tool will search for matching applications and find their linked servers.",
            required=True,
        ),
    ],
            with_files=[
                FileSpec(
                    destination="/opt/scripts/cmdb_query.py",
                    content=script_content,
                ),
            ],
)

# Register the tool
tool_registry.register("servicenow", cmdb_query_tool)
