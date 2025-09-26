#!/usr/bin/env python3
import requests
import json
import os
import sys
import re
from difflib import SequenceMatcher

# ServiceNow configuration
SN_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
SN_USERNAME = os.getenv('SERVICENOW_USERNAME')
SN_PASSWORD = os.getenv('SERVICENOW_PASSWORD')

if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
    error_response = {"error": "Missing required ServiceNow environment variables", "required": ["SERVICENOW_INSTANCE", "SERVICENOW_USERNAME", "SERVICENOW_PASSWORD"]}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)

# Common headers for API requests
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Authentication
AUTH = (SN_USERNAME, SN_PASSWORD)

def normalize_search_term(term):
    """Normalize search term by handling common variations"""
    # Convert to lowercase for case-insensitive matching
    normalized = term.lower().strip()
    
    # Replace common separators with wildcards for flexible matching
    # This handles cases like "dev banking" -> "dev*banking" or "dev-banking"
    variations = [
        normalized,  # Original
        normalized.replace(' ', '-'),  # space to hyphen
        normalized.replace(' ', '_'),  # space to underscore
        normalized.replace(' ', ''),   # remove spaces
        normalized.replace('-', ' '),  # hyphen to space
        normalized.replace('_', ' '),  # underscore to space
        normalized.replace('-', ''),   # remove hyphens
        normalized.replace('_', ''),   # remove underscores
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for variation in variations:
        if variation not in seen:
            seen.add(variation)
            unique_variations.append(variation)
    
    return unique_variations

def calculate_similarity(term1, term2):
    """Calculate similarity between two terms using SequenceMatcher"""
    return SequenceMatcher(None, term1.lower(), term2.lower()).ratio()

def score_application_match(search_term, app_name, app_description=""):
    """Score how well an application matches the search term"""
    search_lower = search_term.lower()
    name_lower = app_name.lower() if app_name else ""
    desc_lower = app_description.lower() if app_description else ""
    
    # Exact match gets highest score
    if search_lower == name_lower:
        return 1.0
    
    # Check if search term is contained in name (high score)
    if search_lower in name_lower:
        return 0.9
    
    # Check if all words from search are in name
    search_words = search_lower.split()
    name_words = re.findall(r'\w+', name_lower)
    if all(any(word in name_word for name_word in name_words) for word in search_words):
        return 0.8
    
    # Check if search term is contained in description
    if search_lower in desc_lower:
        return 0.6
    
    # Use fuzzy matching for partial matches
    name_similarity = calculate_similarity(search_term, app_name)
    desc_similarity = calculate_similarity(search_term, app_description) if app_description else 0
    
    return max(name_similarity, desc_similarity * 0.5)

def generate_search_queries(search_term):
    """Generate multiple search query variations"""
    variations = normalize_search_term(search_term)
    queries = []
    
    for variation in variations:
        # Exact match
        queries.append(f'name={variation}')
        queries.append(f'sys_id={variation}')
        
        # Contains match
        queries.append(f'nameLIKE{variation}')
        queries.append(f'short_descriptionLIKE{variation}')
        
        # Word boundary matches for multi-word terms
        if ' ' in variation or '-' in variation or '_' in variation:
            words = re.findall(r'\w+', variation)
            if len(words) > 1:
                # All words must be present
                word_conditions = [f'nameLIKE{word}' for word in words]
                queries.append('^'.join(word_conditions))
                
                # Any word matches
                for word in words:
                    queries.append(f'nameLIKE{word}')
                    queries.append(f'short_descriptionLIKE{word}')
    
    return queries

def make_request(table_name, params=None, method='GET'):
    """Make authenticated request to ServiceNow API"""
    # Handle both cases: instance name only or full URL
    if SN_INSTANCE.startswith('http'):
        base_url = SN_INSTANCE
    else:
        base_url = f"https://{SN_INSTANCE}.service-now.com"
    
    url = f"{base_url}/api/now/table/{table_name}"
    
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
        error_response = {"error": f"ServiceNow API request failed", "url": url, "details": str(e)}
        print(json.dumps(error_response, indent=2))
        sys.exit(1)

# APM Catalog Query Tool
import argparse

parser = argparse.ArgumentParser(description='Query ServiceNow APM catalog')
parser.add_argument('search_term', help='Term to search for in APM catalog')
args = parser.parse_args()

search_term = args.search_term

# Generate multiple search strategies
search_queries = generate_search_queries(search_term)

# Try different search strategies and collect all results
all_applications = {}
best_score = 0

for query in search_queries:
    try:
        app_params = {
            'sysparm_query': query,
            'sysparm_fields': 'sys_id,name,short_description,operational_status,assigned_to,owned_by,category,subcategory',
            'sysparm_limit': 50
        }
        
        app_results = make_request('cmdb_ci_appl', app_params)
        
        if app_results.get('result'):
            for app in app_results['result']:
                sys_id = app.get('sys_id')
                if sys_id not in all_applications:
                    # Calculate relevance score for this application
                    score = score_application_match(
                        search_term, 
                        app.get('name', ''), 
                        app.get('short_description', '')
                    )
                    
                    application = {
                        "sys_id": sys_id,
                        "name": app.get('name'),
                        "description": app.get('short_description'),
                        "operational_status": app.get('operational_status'),
                        "assigned_to": app.get('assigned_to'),
                        "owned_by": app.get('owned_by'),
                        "category": app.get('category'),
                        "subcategory": app.get('subcategory'),
                        "relevance_score": score
                    }
                    all_applications[sys_id] = application
                    best_score = max(best_score, score)
    
    except Exception as e:
        # Continue with other search strategies if one fails
        continue

# Filter and sort results by relevance
if not all_applications:
    error_response = {"error": "Application not found", "searched": search_term}
    print(json.dumps(error_response, indent=2))
    sys.exit(1)

# Sort applications by relevance score (highest first)
sorted_applications = sorted(
    all_applications.values(), 
    key=lambda x: x['relevance_score'], 
    reverse=True
)

# Remove relevance_score from final output (it was just for sorting)
for app in sorted_applications:
    app.pop('relevance_score', None)

response = {
    "search_term": search_term,
    "applications_found": len(sorted_applications),
    "applications": sorted_applications
}

print(json.dumps(response, indent=2))