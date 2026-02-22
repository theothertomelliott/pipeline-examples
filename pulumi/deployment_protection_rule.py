"""Dynamic resource for GitHub deployment protection rules"""

import traceback
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
        
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 201:
            return pulumi.dynamic.CreateResult(
                id_=f"{env_name}-{props['integration_id']}",
                outs=props
            )
        
        # Handle case where rule already exists
        if resp.status_code == 409:
            # Check if rule already exists
            check_resp = requests.get(url, headers=headers)
            if check_resp.status_code == 200:
                response = check_resp.json()
                rules = response.get("custom_deployment_protection_rules", [])
                for rule in rules:
                    app_id = rule.get("app", {}).get("id")
                    if app_id == props["integration_id"]:
                        return pulumi.dynamic.CreateResult(
                            id_=f"{env_name}-{props['integration_id']}",
                            outs=props
                        )
        
        raise RuntimeError(
            f"Failed to attach protection rule: {resp.status_code} {resp.text}"
        )
    
    def read(self, id_, props):
        print(f"DEBUG: read called with id_={id_}, props type={type(props)}")
        
        # Skip read during refresh to avoid issues
        # Return empty dict for outs to avoid NoneType error
        return pulumi.dynamic.ReadResult(id_=id_, outs={})
    
    def delete(self, id_, props):
        try:
            print(f"DEBUG: delete called with id_={id_}, props type={type(props)}")
            print(f"DEBUG: props content: {props}")
            
            # Handle different prop structures during delete
            if not props or not isinstance(props, dict):
                print(f"DEBUG: Invalid props in delete, returning")
                return None
            
            env_name = props.get("environment")
            token = props.get("token")
            
            print(f"DEBUG: env_name={env_name}, token type={type(token)}")
            
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
                response = resp.json()
                print(f"DEBUG: Rules response: {response}")
                rules = response.get("custom_deployment_protection_rules", [])
                for rule in rules:
                    print(f"DEBUG: Rule type: {type(rule)}, rule content: {rule}")
                    if isinstance(rule, dict):
                        app_id = rule.get("app", {}).get("id")
                        print(f"DEBUG: Comparing app_id: {app_id} with props integration_id: {props.get('integration_id')}")
                        if app_id == props.get("integration_id"):
                            rule_id = rule.get("id")
                            if rule_id:
                                delete_url = (
                                    f"https://api.github.com/repos/{owner}/{repo_name}"
                                    f"/environments/{env_name}/deployment_protection_rules/{rule_id}"
                                )
                                requests.delete(delete_url, headers=headers)
                                break
                    else:
                        print(f"DEBUG: Skipping non-dict rule: {rule}")
            
            return None
        except Exception as e:
            print(f"DEBUG: Exception in delete: {e}")
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            raise

class DeploymentProtectionRule(Resource):
    def __init__(self, name, args, opts=None):
        super().__init__(DeploymentProtectionRuleProvider(), name, args, opts)
