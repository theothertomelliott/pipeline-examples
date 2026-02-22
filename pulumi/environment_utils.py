"""Utility functions for creating GitHub environments with protection rules"""

import pulumi
import pulumi_github as github
from deployment_protection_rule import DeploymentProtectionRule

def create_environment(name, variables=None, protection_rule_id=None, github_token=None):
    """
    Create a GitHub repository environment with optional variables and protection rule.
    
    Args:
        name: Environment name
        variables: Dict of environment variables (e.g., {"ENVIRONMENT": "production"})
        protection_rule_id: GitHub App ID for protection rule (None for no protection)
        github_token: GitHub token for protection rule API calls
    
    Returns:
        Tuple of (environment_resource, protection_rule_resource)
    """
    # Create the environment
    env = github.RepositoryEnvironment(
        f"env-{name}",
        environment=name,
        repository="pipeline-examples",
        wait_timer=0
    )
    
    # Add environment variables if provided
    if variables:
        for var_name, var_value in variables.items():
            resource_name = f"var-{name}-{var_name}"
            
            try:
                github.ActionsEnvironmentVariable(
                    resource_name,
                    repository="pipeline-examples",
                    environment=name,
                    variable_name=var_name,
                    value=var_value,
                    opts=pulumi.ResourceOptions(depends_on=[env])
                )
            except Exception as e:
                # If variable already exists, that's okay
                if "already exists" in str(e).lower():
                    print(f"Variable {var_name} already exists for environment {name}")
                else:
                    raise
    
    # Add protection rule if specified
    protection_rule = None
    if protection_rule_id and github_token:
        protection_rule = DeploymentProtectionRule(
            f"protection-{name}",
            args={
                "environment": env.environment,
                "integration_id": protection_rule_id,
                "token": github_token,
            },
            opts=pulumi.ResourceOptions(depends_on=[env])
        )
    
    return env, protection_rule
