from mcp.server.fastmcp import FastMCP
import sys

# Initialize FastMCP server
mcp = FastMCP("lab-mcp-server")

# Import features to register them
# We do this inside main or just let side-effects happen on import if designed that way.
# For this structure, we will import them here so the decorators run.

from lab_mcp_server.tools import calculator
from lab_mcp_server.resources import system_info
from lab_mcp_server.prompts import code_review

def main():
    """Run the MCP server."""
    # FastMCP handles the stdio connection automatically when run() is called
    mcp.run()

if __name__ == "__main__":
    main()
