from dataengineeringutils3.pulumi import Tagger
from pulumi import Config, ResourceOptions
from pulumi_aws import get_caller_identity
from pulumi_aws.codebuild import (
    Project,
    ProjectArtifactsArgs,
    ProjectCacheArgs,
    ProjectEnvironmentArgs,
    ProjectEnvironmentEnvironmentVariableArgs,
    ProjectSourceArgs,
    Webhook,
    WebhookFilterGroupArgs,
    WebhookFilterGroupFilterArgs,
)
from pulumi_aws.codebuild.source_credential import SourceCredential
from pulumi_aws.iam import (
    GetPolicyDocumentStatementArgs,
    GetPolicyDocumentStatementPrincipalArgs,
    Role,
    RolePolicy,
    get_policy_document,
)

tagger = Tagger(
    environment_name="alpha",
    source_code=(
        "https://github.com/moj-analytical-services/"
        "data-engineering-database-access-deploy"
    ),
)

GIT_CRYPT_KEY = Config().require("git_crypt_key")
GITHUB_TOKEN = Config().require("github_token")

account_id = get_caller_identity().account_id

assume_role_policy = get_policy_document(
    statements=[
        GetPolicyDocumentStatementArgs(
            actions=["sts:AssumeRole"],
            effect="Allow",
            principals=[
                GetPolicyDocumentStatementPrincipalArgs(
                    identifiers=["codebuild.amazonaws.com"], type="Service"
                )
            ],
        )
    ]
)

serviceRole = Role(
    resource_name="this",
    name="database-access-codebuild-service-role",
    assume_role_policy=assume_role_policy.json,
    force_detach_policies=True,
    tags=tagger.create_tags("database-access-codebuild-service-role"),
)

policy = get_policy_document(
    statements=[
        GetPolicyDocumentStatementArgs(
            actions=["iam:*"],
            effect="Allow",
            resources=[
                f"arn:aws:iam::{account_id}:role/alpha_user_*",
                f"arn:aws:iam::{account_id}:role/alpha_app_*",
            ],
            sid="IamPolicy",
        ),
        GetPolicyDocumentStatementArgs(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            effect="Allow",
            resources=["*"],
            sid="CloudWatchLogsPolicy",
        ),
        GetPolicyDocumentStatementArgs(
            actions=["s3:*"],
            effect="Allow",
            resources=[
                "arn:aws:s3:::data-engineering-pulumi.analytics.justice.gov.uk",
                "arn:aws:s3:::data-engineering-pulumi.analytics.justice.gov.uk/*",
            ],
            sid="S3Policy",
        ),
    ]
)

serviceRolePolicy = RolePolicy(
    resource_name="this",
    policy=policy.json,
    role=serviceRole.id,
    opts=ResourceOptions(parent=serviceRole),
)

sourceCredential = SourceCredential(
    resource_name="this",
    auth_type="PERSONAL_ACCESS_TOKEN",
    server_type="GITHUB",
    token=GITHUB_TOKEN,
)

pullRequestProject = Project(
    resource_name="pull-request",
    name="database-access-pull-request",
    description="Runs pulumi preview on database access pull requests",
    service_role=serviceRole.arn,
    cache=ProjectCacheArgs(type="NO_CACHE"),
    badge_enabled=False,
    artifacts=ProjectArtifactsArgs(type="NO_ARTIFACTS"),
    environment=ProjectEnvironmentArgs(
        compute_type="BUILD_GENERAL1_SMALL",
        type="LINUX_CONTAINER",
        image="aws/codebuild/standard:5.0",
        environment_variables=[
            ProjectEnvironmentEnvironmentVariableArgs(
                name="GIT_CRYPT_KEY", value=GIT_CRYPT_KEY
            )
        ],
    ),
    source=ProjectSourceArgs(
        type="GITHUB",
        git_clone_depth=1,
        location=(
            "https://github.com/moj-analytical-services/"
            "data-engineering-database-access.git"
        ),
        buildspec=".codebuild/buildspec_pull_request.yaml",
        report_build_status=True,
    ),
    tags=tagger.create_tags("database-access-pull-request"),
    opts=ResourceOptions(depends_on=[serviceRole]),
)

pullRequestWebhook = Webhook(
    resource_name="pull-request",
    filter_groups=[
        WebhookFilterGroupArgs(
            filters=[
                WebhookFilterGroupFilterArgs(
                    pattern=(
                        "PULL_REQUEST_CREATED,"
                        "PULL_REQUEST_UPDATED,"
                        "PULL_REQUEST_REOPENED"
                    ),
                    type="EVENT",
                )
            ]
        )
    ],
    project_name=pullRequestProject.name,
    opts=ResourceOptions(parent=pullRequestProject),
)

pushProject = Project(
    resource_name="push",
    name="database-access-push",
    description="Runs pulumi up on database access pushes to master",
    service_role=serviceRole.arn,
    cache=ProjectCacheArgs(type="NO_CACHE"),
    badge_enabled=False,
    artifacts=ProjectArtifactsArgs(type="NO_ARTIFACTS"),
    environment=ProjectEnvironmentArgs(
        compute_type="BUILD_GENERAL1_SMALL",
        type="LINUX_CONTAINER",
        image="aws/codebuild/standard:5.0",
        environment_variables=[
            ProjectEnvironmentEnvironmentVariableArgs(
                name="GIT_CRYPT_KEY", value=GIT_CRYPT_KEY
            )
        ],
    ),
    source=ProjectSourceArgs(
        type="GITHUB",
        git_clone_depth=1,
        location=(
            "https://github.com/moj-analytical-services/"
            "data-engineering-database-access.git"
        ),
        buildspec=".codebuild/buildspec_push.yaml",
        report_build_status=True,
    ),
    tags=tagger.create_tags("database-access-push"),
    opts=ResourceOptions(depends_on=[serviceRole]),
)

pushWebhook = Webhook(
    resource_name="push",
    filter_groups=[
        WebhookFilterGroupArgs(
            filters=[
                WebhookFilterGroupFilterArgs(pattern="PUSH", type="EVENT"),
                WebhookFilterGroupFilterArgs(
                    pattern="^refs/heads/main$", type="HEAD_REF"
                ),
            ]
        )
    ],
    project_name=pushProject.name,
    opts=ResourceOptions(parent=pushProject),
)
