from lab_mcp_server.server import mcp

@mcp.tool()
def calculate(operation: str, a: float, b: float) -> float:
    """
    Perform a basic mathematical operation.

    Args:
        operation: The operation to perform. Supported: "add", "subtract", "multiply", "divide".
        a: The first number.
        b: The second number.
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")
