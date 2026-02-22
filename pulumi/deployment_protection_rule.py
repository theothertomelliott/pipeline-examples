"""Dynamic resource for GitHub deployment protection rules"""

import pulumi
import pulumi_github as github
import json
import requests
from pulumi.dynamic import Resource, ResourceProvider

class DeploymentProtectionRuleProvider(ResourceProvider):
    def create(self, props):
        print(f"DEBUG: create called with props: {props}")
        
        # Handle missing props gracefully
        if not props:
            raise RuntimeError("No props provided to dynamic resource")
        
        env_name = props.get("environment")
        token = props.get("token")
        
        if not env_name:
            raise RuntimeError(f"Missing 'environment' in props: {props}")
        if not token:
            raise RuntimeError(f"Missing 'token' in props: {props}")
        
        owner = "theothertomelliott"
        repo_name = "pipeline-examples"
        url = (
            f"https://api.github.com/repos/{owner}/{repo_name}"
            f"/environments/{env_name}/deployment_protection_rules"
        )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        payload = {
            "integration_id": 2918233
        }
        
        resp = requests.post(url, headers=headers, data=json.dumps(payload))
        if resp.status_code not in (200, 201, 204):
            # If the protection rule already exists, that's okay
            if resp.status_code == 422 and "already_exists" in resp.text:
                print(f"Protection rule already exists for environment {env_name}")
                return pulumi.dynamic.CreateResult(
                    id_=f"{env_name}-{props['integration_id']}",
                    outs=props
                )
            raise RuntimeError(
                f"Failed to attach protection rule: {resp.status_code} {resp.text}"
            )
        
        return pulumi.dynamic.CreateResult(
            id_=f"{env_name}-{props['integration_id']}",
            outs=props
        )
    
    def read(self, id_, props):
        print(f"DEBUG: read called with id_={id_}, props type={type(props)}")
        
        # Skip read during refresh to avoid issues
        # Return empty dict for outs to avoid NoneType error
        return pulumi.dynamic.ReadResult(id_=id_, outs={})
    
    def delete(self, id_, props):
        print(f"DEBUG: delete called with id_={id_}, props={props}")
        
        env_name = props.get("environment")
        token = props.get("token")
        
        if not env_name or not token:
            print(f"DEBUG: Missing props in delete, returning")
            return None
        
        owner = "theothertomelliott"
        repo_name = "pipeline-examples"
        
        # Get the rule ID first
        list_url = (
            f"https://api.github.com/repos/{owner}/{repo_name}"
            f"/environments/{env_name}/deployment_protection_rules"
        )
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        resp = requests.get(list_url, headers=headers)
        if resp.status_code == 200:
            rules = resp.json()
            for rule in rules:
                if rule.get("integration_id") == props.get("integration_id"):
                    rule_id = rule.get("id")
                    if rule_id:
                        delete_url = (
                            f"https://api.github.com/repos/{owner}/{repo_name}"
                            f"/environments/{env_name}/deployment_protection_rules/{rule_id}"
                        )
                        requests.delete(delete_url, headers=headers)
                        break
        
        return None

class DeploymentProtectionRule(Resource):
    def __init__(self, name, args, opts=None):
        super().__init__(DeploymentProtectionRuleProvider(), name, args, opts)
