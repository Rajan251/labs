from lab_mcp_server.server import mcp
import platform
import sys

@mcp.resource("system://info")
def get_system_info() -> str:
    """Get basic system information."""
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python_version": sys.version,
    }
    return str(info)
