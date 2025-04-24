# databricks-mcp-template

A local [Model Context Protocol (MCP)](https://modelcontext.org/) server designed to work with [Claude Desktop](https://www.anthropic.com/index/claude-desktop) or any other MCP-compatible LLM client. This server allows tools to be called dynamically based on user input — ideal for enriching metadata, running Databricks queries, or augmenting Claude's capabilities.

---

## Server Setup Instructions

### 1. Clone this repository

```bash
git clone https://github.com/emma-mckee-pw/databricks-mcp-template
cd databricks-mcp-template
```
### 2. Install dependencies
```bash
npm install
# You need Node.js (v18+) and npm. If not installed, run:
brew install node
```
### 3. Set up your environment
Copy the .env.example file:
```bash
cp .env.example .env
```
Open the .env file (nano, texteditor, etc) and add your databricks token:
```bash
open -a TextEdit .env
```
### 4. Start the MCP server
```bash
./start_server.sh
```
## Connect Claude Desktop to Server
See https://modelcontextprotocol.io/quickstart/user for instructions


