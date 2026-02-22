import modal
from fastapi import Request
import json
import os
import time
import jwt
import requests

image = modal.Image.debian_slim().uv_pip_install(
    "fastapi[standard]", 
    "PyJWT", 
    "cryptography", 
    "requests"
)
app = modal.App(name="github-approver", image=image)

@app.function(
    secrets=[modal.Secret.from_name("github-app")]
)
@modal.fastapi_endpoint(
    method="POST",
    docs=True  # adds interactive documentation in the browser
)
def handle(request: Request, body: dict):
    # Get App ID and PEM from env var
    client_id = os.environ["CLIENT_ID"] 
    signing_key = os.environ["PRIVATE_KEY"]
    
    # Clean up any whitespace
    client_id = client_id.strip()
    
    payload = {
        # Issued at time
        'iat': int(time.time()),
        # JWT expiration time (10 minutes maximum)
        'exp': int(time.time()) + 600,

        # GitHub Client ID
        'iss': client_id
    }

    # Create JWT
    encoded_jwt = jwt.encode(payload, signing_key, algorithm='RS256')

    # Get installation ID from webhook payload
    installation_id = body.get("installation", {}).get("id")
    if not installation_id:
        print("No installation ID found in webhook payload")
        return "ERROR: No installation ID"
    
    # Get repository ID from webhook payload
    repository_id = body.get("repository", {}).get("id")
    if not repository_id:
        print("No repository ID found in webhook payload")
        return "ERROR: No repository ID"

    # Generate install token
    token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {encoded_jwt}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    
    token_payload = {
        "repository_ids": [repository_id],
        "permissions": {
            "deployments": "write"
        }
    }
    
    try:
        response = requests.post(token_url, headers=headers, json=token_payload)
        response.raise_for_status()
        
        token_data = response.json()
        install_token = token_data.get("token")
        
    except requests.exceptions.RequestException as e:
        print(f"Error generating install token: {e}")
        print(f"Response: {response.text if 'response' in locals() else 'No response'}")
        return "ERROR: Failed to generate install token"
    
    # Get deployment callback URL from webhook payload
    callback_url = body.get("deployment_callback_url")
    if not callback_url:
        print("No deployment callback URL found in webhook payload")
        return "ERROR: No callback URL"
    
    # Get environment name from webhook payload
    environment_name = body.get("environment")
    if not environment_name:
        print("No environment name found in webhook payload")
        return "ERROR: No environment name"
    
    # For demo purposes, automatically approve the deployment
    # In a real app, you might check conditions, ask for approval, etc.
    approval_payload = {
        "environment_name": environment_name,
        "state": "approved",
        "comment": "Deployment approved by Pipeline Approvals app"
    }
    
    # Use the install token to approve the deployment
    approval_headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {install_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    
    # Approve the deployment
    try:
        approval_response = requests.post(
            callback_url, 
            headers=approval_headers, 
            json=approval_payload
        )
        
        if approval_response.status_code == 200 or approval_response.status_code == 204:
            print(f"Deployment approved successfully!")
            return "Deployment approved"
        else:
            print(f"Unexpected status code: {approval_response.status_code}")
            print(f"Approval response: {approval_response.text}")
            return f"ERROR: Unexpected status {approval_response.status_code}"
        
    except requests.exceptions.RequestException as e:
        print(f"Error approving deployment: {e}")
        print(f"Approval response: {approval_response.text if 'approval_response' in locals() else 'No response'}")
        return "ERROR: Failed to approve deployment"