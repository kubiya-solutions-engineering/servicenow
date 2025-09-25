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

# Read the audit ticket script content directly from file
scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
with open(scripts_dir / "audit_ticket.py", "r") as f:
    script_content = f.read()

# Define the tool before any potential imports can occur
audit_ticket_tool = ServiceNowTool(
    name="servicenow_audit_ticket",
    description="Create ServiceNow audit tickets to track who, what, when for server operations and maintain compliance audit trail",
    content="""
set -e
python -m venv /opt/venv > /dev/null
. /opt/venv/bin/activate > /dev/null
pip install requests==2.32.3 2>&1 | grep -v '[notice]'

# Run the audit ticket script
python /opt/scripts/audit_ticket.py --user "{{ .user }}" --action "{{ .action }}" --application "{{ .application }}" --servers "{{ .servers }}" --status "{{ .status }}" --details "{{ .details }}" --teams_channel "{{ .teams_channel }}" --aws_account "{{ .aws_account }}" --aws_region "{{ .aws_region }}"
""",
    args=[
        Arg(
            name="user",
            description="User who initiated the action (email address or username)",
            required=True,
        ),
        Arg(
            name="action",
            description="Action performed (e.g., 'server_startup', 'server_shutdown', 'application_deployment')",
            required=True,
        ),
        Arg(
            name="application",
            description="Application name or identifier that was affected",
            required=True,
        ),
        Arg(
            name="servers",
            description="Comma-separated list of server names/IDs that were affected by the operation",
            required=True,
        ),
        Arg(
            name="status",
            description="Operation status: 'success', 'failure', or 'partial'",
            required=True,
        ),
        Arg(
            name="details",
            description="Additional details about the operation (optional)",
            required=False,
        ),
        Arg(
            name="teams_channel",
            description="Microsoft Teams channel where the request originated (optional)",
            required=False,
        ),
        Arg(
            name="aws_account",
            description="AWS account ID where servers are located (optional)",
            required=False,
        ),
        Arg(
            name="aws_region",
            description="AWS region where servers are located (optional)",
            required=False,
        ),
    ],
    with_files=[
        FileSpec(
            destination="/opt/scripts/audit_ticket.py",
            content=script_content,
        ),
    ],
)

# Register the tool
tool_registry.register("servicenow", audit_ticket_tool)
