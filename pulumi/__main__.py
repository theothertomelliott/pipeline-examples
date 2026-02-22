"""A GitHub Python Pulumi program"""

import json
import pulumi
import pulumi_github as github
from environment_utils import create_environment

config = pulumi.Config("github")
github_token = config.require_secret("token")

# Create staging environment (no protection rule)
staging_env, _ = create_environment(
    name="staging",
    variables={"ENVIRONMENT": "staging"},
)

# Create production environments with protection rule
production_envs = []
for i in range(1, 4):
    env, protection = create_environment(
        name=f"production{i}",
        variables={"ENVIRONMENT": f"production{i}"},
        protection_rule_id=2918233,  # Pipeline approvals app
        github_token=github_token
    )
    production_envs.append((env, protection))

# Export environment names
pulumi.export('stagingEnvironment', staging_env.environment)
pulumi.export('productionEnvironments', [env.environment for env, _ in production_envs])

# Create a GitHub repository variable for production environments
production_env_list = [env.environment.apply(lambda e: str(e)) for env, _ in production_envs]
production_envs_json = pulumi.Output.all(*production_env_list).apply(
    lambda envs: json.dumps(envs)
)

github.ActionsVariable(
    "production-environments",
    repository="pipeline-examples",
    variable_name="PRODUCTION_ENVIRONMENTS",
    value=production_envs_json
)
