from typing import List, Optional, Dict, Any
from kubiya_sdk.tools import Tool, Arg, FileSpec

SERVICENOW_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/ServiceNow_logo.svg/2560px-ServiceNow_logo.svg.png"

DEFAULT_MERMAID = """
```mermaid
classDiagram
    class Tool {
        <<interface>>
        +get_args()
        +get_content()
        +get_image()
    }
    class ServiceNowTool {
        -content: str
        -args: List[Arg]
        -image: str
        +__init__(name, description, content, args, image)
        +get_args()
        +get_content()
        +get_image()
        +get_file_specs()
        +validate_args(args)
        +get_error_message(args)
        +get_environment()
    }
    Tool <|-- ServiceNowTool
```
"""

class ServiceNowTool(Tool):
    """Base class for all ServiceNow tools."""
    
    name: str
    description: str
    content: str = ""
    args: List[Arg] = []
    image: str = "python:3.11-slim"
    icon_url: str = SERVICENOW_ICON_URL
    type: str = "docker"
    mermaid: str = DEFAULT_MERMAID
    
    def __init__(self, name, description, content, args=None, image="python:3.11-slim", **kwargs):
        # ServiceNow API setup and common imports
        servicenow_setup = """#!/usr/bin/env python3
import requests
import json
import os
import sys
from urllib.parse import urljoin

# ServiceNow configuration
SN_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
SN_USERNAME = os.getenv('SERVICENOW_USERNAME')
SN_PASSWORD = os.getenv('SERVICENOW_PASSWORD')
# Using standard api/now endpoint - no version needed

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    print("Error: Missing required ServiceNow environment variables")
    print("Required: SERVICENOW_INSTANCE, SERVICENOW_USERNAME, SERVICENOW_PASSWORD")
    sys.exit(1)

# Base URL for ServiceNow API
BASE_URL = f"https://{SN_INSTANCE}.service-now.com/api/now"

# Common headers for API requests
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Authentication
AUTH = (SN_USERNAME, SN_PASSWORD)

def make_request(endpoint, params=None, method='GET'):
    \"\"\"Make authenticated request to ServiceNow API\"\"\"
    url = urljoin(BASE_URL, endpoint)
    
    try:
        if method == 'GET':
            response = requests.get(url, auth=AUTH, headers=HEADERS, params=params)
        elif method == 'POST':
            response = requests.post(url, auth=AUTH, headers=HEADERS, json=params)
        elif method == 'PUT':
            response = requests.put(url, auth=AUTH, headers=HEADERS, json=params)
        elif method == 'DELETE':
            response = requests.delete(url, auth=AUTH, headers=HEADERS)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {str(e)}")
        sys.exit(1)

def format_output(data, title="ServiceNow API Response"):
    \"\"\"Format and print API response data\"\"\"
    print(f"=== {title} ===")
    print(json.dumps(data, indent=2))
"""
        
        full_content = f"{servicenow_setup}\n{content}"

        # Merge default ServiceNow config with any additional kwargs
        init_kwargs = {
            'name': name,
            'description': description,
            'content': full_content,
            'args': args or [],
            'image': image,
            'icon_url': SERVICENOW_ICON_URL,
            'type': "docker",
            'env': ["SERVICENOW_INSTANCE", "SERVICENOW_USERNAME"],
            'secrets': ["SERVICENOW_PASSWORD"],
        }
        
        # Add any additional kwargs (like with_files, mermaid, etc.)
        init_kwargs.update(kwargs)
        
        super().__init__(**init_kwargs)

    def get_args(self) -> List[Arg]:
        """Return the tool's arguments."""
        return self.args

    def get_content(self) -> str:
        """Return the tool's Python script content."""
        return self.content

    def get_image(self) -> str:
        """Return the Docker image to use."""
        return self.image

    def validate_args(self, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments."""
        required_args = [arg.name for arg in self.args if arg.required]
        return all(arg in args and args[arg] for arg in required_args)

    def get_error_message(self, args: Dict[str, Any]) -> Optional[str]:
        """Return error message if arguments are invalid."""
        missing_args = []
        for arg in self.args:
            if arg.required and (arg.name not in args or not args[arg.name]):
                missing_args.append(arg.name)
        
        if missing_args:
            return f"Missing required arguments: {', '.join(missing_args)}"
        return None
