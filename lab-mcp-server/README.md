# Lab MCP Server

A comprehensive example of a Model Context Protocol (MCP) server implementation in Python.

## Overview

This project serves as a template and working example for developers to build their own MCP servers. It demonstrates how to:

- Set up a Python-based MCP server.
- Register **Tools** (executable functions).
- Register **Resources** (read-only data sources).
- Register **Prompts** (reusable prompt templates).

## Project Structure

```text
lab-mcp-server/
├── README.md           # This file
├── pyproject.toml      # Project configuration and dependencies
├── src/
│   └── lab_mcp_server/
│       ├── server.py   # Main server instance and configuration
│       ├── tools/      # Tool implementations
│       ├── resources/  # Resource implementations
│       └── prompts/    # Prompt implementations
```

## Prerequisites

- Python 3.10 or higher
- `uv` (recommended) or `pip`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd lab-mcp-server
    ```

2.  **Install dependencies:**
    Using `uv` (recommended):
    ```bash
    uv sync
    ```
    Or using `pip`:
    ```bash
    pip install .
    ```

## Usage

### Running the Server

The server is designed to run over stdio. You can run it directly:

```bash
# If installed via pip/uv
lab-mcp-server

# Or running as a module
python -m lab_mcp_server
```

*Note: The server will wait for MCP protocol messages on stdin. It will not output anything visible unless it receives a valid request.*

### Inspecting with MCP Inspector

To verify the server is working correctly, use the MCP Inspector (requires Node.js):

```bash
npx @modelcontextprotocol/inspector python -m lab_mcp_server
```

### Configuring Claude Desktop

To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lab-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/lab-mcp-server",
        "run",
        "lab-mcp-server"
      ]
    }
  }
}
```

## Features

### Tools
- `calculate`: A simple calculator that performs addition and subtraction.

### Resources
- `system://info`: Returns basic system information (platform, python version).

### Prompts
- `code_review`: A prompt template for reviewing code.

## Development

To add new features:

1.  Create a new file in `src/lab_mcp_server/tools/`, `resources/`, or `prompts/`.
2.  Implement your logic.
3.  Import and register it in `src/lab_mcp_server/server.py`.
