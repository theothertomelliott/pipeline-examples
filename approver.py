import modal
from fastapi import Request
import json
import os
import time
import jwt

image = modal.Image.debian_slim().uv_pip_install("fastapi[standard]", "PyJWT", "cryptography")
app = modal.App(name="github-approver", image=image)

@app.function(
    secrets=[modal.Secret.from_name("github-app")]
)
@modal.fastapi_endpoint(
    method="POST",
    docs=True  # adds interactive documentation in the browser
)
def handle(request: Request, body: dict):
    headers = dict(request.headers)
    print(json.dumps(headers, indent=4, sort_keys=True))

    print(json.dumps(body, indent=4, sort_keys=True))

    # Get Client ID and PEM from env var
    client_id = os.environ["CLIENT_ID"]
    signing_key = os.environ["PRIVATE_KEY"]
    
    payload = {
        # Issued at time
        'iat': int(time.time()),
        # JWT expiration time (10 minutes maximum)
        'exp': int(time.time()) + 600,

        # GitHub App's client ID
        'iss': client_id
    }

    # Create JWT
    encoded_jwt = jwt.encode(payload, signing_key, algorithm='RS256')

    print(f"JWT: {encoded_jwt}")

    return "OK"