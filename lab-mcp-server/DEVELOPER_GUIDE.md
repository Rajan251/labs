# Developer Guide

This guide provides detailed information on the architecture of the Lab MCP Server and how to extend it.

## Architecture

The server is built using the `mcp` Python SDK, specifically the `FastMCP` class, which provides a high-level, decorator-based API.

### Core Components

1.  **Server Instance (`server.py`)**: The central point where the `FastMCP` application is initialized. It imports other modules to register their components.
2.  **Tools (`tools/`)**: Functions that the LLM can execute. They are decorated with `@mcp.tool()`.
3.  **Resources (`resources/`)**: Data sources that the LLM can read. They are decorated with `@mcp.resource()`.
4.  **Prompts (`prompts/`)**: Reusable templates for interacting with the LLM. They are decorated with `@mcp.prompt()`.

## Adding New Features

### Adding a Tool

Tools are Python functions that perform actions or calculations.

1.  Create a new file in `src/lab_mcp_server/tools/` (e.g., `weather.py`).
2.  Import the `mcp` instance:
    ```python
    from lab_mcp_server.server import mcp
    ```
3.  Define your function and decorate it:
    ```python
    @mcp.tool()
    def get_weather(city: str) -> str:
        """Get the weather for a city."""
        return f"The weather in {city} is sunny."
    ```
4.  Register it in `src/lab_mcp_server/tools/__init__.py`:
    ```python
    from . import weather
    ```
5.  Ensure `src/lab_mcp_server/server.py` imports the `tools` package (already done by default).

### Adding a Resource

Resources are read-only data exposed via a URI scheme.

1.  Create a new file in `src/lab_mcp_server/resources/`.
2.  Define the resource:
    ```python
    @mcp.resource("my-scheme://my-resource")
    def my_resource() -> str:
        return "Resource content"
    ```

### Adding a Prompt

Prompts are templates that help the LLM generate specific content.

1.  Create a new file in `src/lab_mcp_server/prompts/`.
2.  Define the prompt:
    ```python
    @mcp.prompt()
    def my_prompt(arg: str) -> str:
        return f"Please do something with {arg}"
    ```

## Debugging

Use the MCP Inspector to debug your server. It acts as a client and allows you to test tools and resources interactively.

```bash
npx @modelcontextprotocol/inspector python -m lab_mcp_server
```

## Deployment

To deploy this server, you simply need to ensure Python is installed and the dependencies are available. The server communicates over standard input/output (stdio), so it can be integrated into any MCP-compliant host (like Claude Desktop or an IDE extension) by pointing the host to the execution command.
