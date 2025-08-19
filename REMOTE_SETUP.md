# Remote MCP Server Setup

This guide explains how to set up the FastMCP server for remote access via HTTP transport.

## Quick Start

1. **Start the remote server**:
   ```bash
   ./start_remote_server.sh
   ```
   
   Or with custom host/port:
   ```bash
   ./start_remote_server.sh 192.168.1.100 8000
   ```

2. **Configure Claude Desktop for remote connection**:
   Update your Claude Desktop config file with:
   ```json
   {
     "mcpServers": {
       "databricks-remote": {
         "command": "_disabled_for_remote",
         "args": ["_disabled_for_remote"],
         "env": {
           "_comment": "This server is configured for remote HTTP access"
         },
         "transport": {
           "type": "http",
           "host": "your-server-hostname-or-ip", 
           "port": 8000
         }
       }
     }
   }
   ```

3. **Replace placeholders**:
   - `your-server-hostname-or-ip`: Use the actual IP address or hostname of your server
   - `8000`: Use the actual port if you changed it from the default

## Server Configuration

The server can be configured using environment variables:

- `MCP_HOST`: Host to bind to (default: "0.0.0.0" - all interfaces)
- `MCP_PORT`: Port to listen on (default: "8000")

Example:
```bash
export MCP_HOST="192.168.1.100"
export MCP_PORT="9000"
./start_remote_server.sh
```

## Security Considerations

- The server binds to all interfaces (`0.0.0.0`) by default for remote access
- Consider using a firewall to restrict access to specific clients
- For production use, consider adding authentication and HTTPS support
- Ensure your Databricks credentials are properly secured in the `.env` file

## Troubleshooting

1. **Connection refused**: Check if the server is running and the port is not blocked by firewall
2. **Wrong host/port**: Verify the IP address and port in both server startup and Claude Desktop config
3. **Databricks connection issues**: Ensure the `.env` file contains valid Databricks credentials

## Differences from Local Setup

- Uses HTTP transport instead of stdio
- Server runs as a web service on specified host/port
- Claude Desktop connects via HTTP instead of spawning a subprocess
- No need to specify file paths in Claude Desktop config