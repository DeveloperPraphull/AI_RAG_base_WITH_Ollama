from mcp.server.fastmcp import FastMCP

from app.services.github_service import push_code

mcp = FastMCP("github-tools")


@mcp.tool()
def push_code_to_github(
    branch_name: str,
    commit_message: str
):

    return push_code(
        branch_name,
        commit_message
    )