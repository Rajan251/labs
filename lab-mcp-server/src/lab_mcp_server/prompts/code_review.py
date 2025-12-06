from lab_mcp_server.server import mcp

@mcp.prompt()
def code_review(code: str) -> str:
    """
    Create a prompt for reviewing code.

    Args:
        code: The code to review.
    """
    return f"""Please review the following code for bugs, style issues, and performance improvements:

```python
{code}
```
"""
