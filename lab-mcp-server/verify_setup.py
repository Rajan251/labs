import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

try:
    from lab_mcp_server.server import mcp
    print("Successfully imported server.")
    
    # Check if tools are registered (FastMCP stores them internally)
    # Accessing private members for verification purposes only
    print(f"Server name: {mcp.name}")
    
    # We can't easily list tools without running the server, but import success is a good sign.
    # Let's try to import the specific modules to ensure no syntax errors.
    from lab_mcp_server.tools import calculator
    from lab_mcp_server.resources import system_info
    from lab_mcp_server.prompts import code_review
    print("Successfully imported all feature modules.")

except Exception as e:
    print(f"Verification failed: {e}")
    sys.exit(1)
