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

# Read the identity check script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "identity_check.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
identity_check_tool = ServiceNowTool(
    name="servicenow_identity_check",
    description="Check user's identity (via email or Teams) against ServiceNow roles and entitlement tables",
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install requests==2.32.3 2>&1 | grep -v '[notice]'

# Run the identity check script
python /opt/scripts/identity_check.py "{{ .user_identifier }}"
""",
    args=[
        Arg(
            name="user_identifier",
            description="User identifier to check (email address, username, or sys_id)",
            required=True,
        ),
    ],
            with_files=[
                FileSpec(
                    destination="/opt/scripts/identity_check.py",
                    content=script_content,
                ),
            ],
    mermaid="""
    sequenceDiagram
        participant A as Agent
        participant S as ServiceNow
        participant U as User System

        A ->> S: Check User Identity
        S ->> U: Query User Record
        S ->> U: Query User Roles
        S ->> U: Query Group Memberships
        S ->> U: Query Entitlements
        U -->> S: Return User Data
        S -->> A: Identity Information
    """,
)

# Register the tool
tool_registry.register("servicenow", identity_check_tool)