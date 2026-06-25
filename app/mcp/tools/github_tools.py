from app.mcp.mcp_instance import mcp

from app.services.github_service import (
    create_branch,
    switch_branch,
    push_branch,
    create_and_push_branch,
)

@mcp.tool()
def create_git_branch(
    branch_name: str
):
    return create_branch(branch_name)

@mcp.tool()
def switch_git_branch(
    branch_name: str
):
    return switch_branch(branch_name)

@mcp.tool()
def push_git_branch(
    branch_name: str
):
    return push_branch(branch_name)


@mcp.tool()
def create_and_push_git_branch(
    branch_name: str,
    commit_message: str
):
    return create_and_push_branch(
        branch_name,
        commit_message
    )