<<<<<<< HEAD
# databricks-mcp-template

A local [Model Context Protocol (MCP)](https://modelcontext.org/) server designed to work with [Claude Desktop](https://www.anthropic.com/index/claude-desktop) or any other MCP-compatible LLM client. This server allows tools to be called dynamically based on user input — ideal for enriching metadata, running Databricks queries, or augmenting Claude's capabilities.

---

# Server Setup Instructions
## 1. Verify Node.js is Installed (Required by MCP)

This project uses the Model Context Protocol (MCP) which requires Node.js under the hood — even for Python-based servers.

To check if Node is installed:
```bash
node --version
```
if not installed, download Node.js from https://nodejs.org and install it before continuing.

## 2. Clone this repository

```bash
git clone https://github.com/emma-mckee-pw/databricks-mcp-template
cd databricks-mcp-template
```

## 3. Python Environment Setup
### Option A: Use ```uv``` (recommended)
Add this right after cloning:
```bash
# Create a virtual environment
uv venv

# Sync environment (uses uv.lock if present, or falls back to pyproject.toml)
uv pip sync

# Development Mode (editable install)
uv pip install -e .
```
If ```uv``` is not installed:
```bash
# Install uv if you don't already have it:
curl -Ls https://astral.sh/uv/install.sh | sh
```
Then retry the first commands in step 3

### Option B: Use traditional pip
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```
## 4. Set up your environment
Copy the .env.example file:
```bash
cp .env.example .env
```
Open the .env file (nano, texteditor, etc) and add your databricks token:
```bash
open -a TextEdit .env
```
## 5. Start the MCP server
```bash
./start_server.sh
```
# Connect Claude Desktop to Server
You can also follow the official guide: https://modelcontextprotocol.io/quickstart/user for detailed generic instructions.
### 1. Open Claude Desktop Settings
  - MacOS: Click the Claude menu in your macOS top bar and select Settings
  - Windows: Right-click the Claude icon in your system tray (bottom right corner of your taskbar). Choose "Settings…" from the context menu.

(Note: This is not the in-app settings under your Claude user profile)

## 2. Enable Developer Mode
- In the left sidebar of the Settings window, click Developer
- Then click Edit Config
This opens the config file:
  - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
  - Windows: %APPDATA%\Claude\claude_desktop_config.json

If the file doesn’t exist, Claude will create it for you.

## 3. Configure MCP Server Connection
Replace the contents of the Claude Desktop config file with the structure provided in:
- claude_desktop_config.example.json in this repository

Then update file paths based on your operating system:

**On macOS:**
- Replace any path that looks like:
```
/Users/<your_username>/
```
- With your actual macOS username or full path.
Example:
```
/Users/emma/databricks-mcp-template/start_server.sh
```
**On Windows:**
- Replace the placeholder path with your Windows user directory, using either of the following:
```
C:/Users/your-username/databricks-mcp-template/start_server.sh
```
OR
```
C:\\Users\\your-username\\databricks-mcp-template\\start_server.sh
```
- Both slashes (/) and double backslashes (\\) are valid.

**Do not blindly overwrite your config. Always review the structure and file paths before saving, especially if you have other tools already configured.**

## 4. Restart Claude
After updating your configuration file, you need to restart Claude for Desktop.

Upon restarting, you should see a hammer icon in the bottom of the input box and a black lable indicating you are connected to Purplewave-data:

<img width="749" alt="image" src="https://github.com/user-attachments/assets/69d834cf-6c59-457e-9ce4-d1f624ae6f37" />

After clicking on the hammer icon, you should see the tools that come with the Filesystem MCP Server:

<img width="522" alt="image" src="https://github.com/user-attachments/assets/b58fdf0f-58af-44f0-b272-99c8565b6454" />

For troubleshooting assistance, see https://modelcontextprotocol.io/quickstart/user#troubleshooting

## 5. Test it out!
The project with the instruction prompt specific to this server is called Item Basics Assistant
- Navigate to project under "Projects" in the ribbon on the left hand side
- Select the Item Basics Assistant project space
- Try asking Claude a question about our Purple Wave Item Data! 

=======
# databricks-mcp-template

A local [Model Context Protocol (MCP)](https://modelcontext.org/) server designed to work with [Claude Desktop](https://www.anthropic.com/index/claude-desktop) or any other MCP-compatible LLM client. This server allows tools to be called dynamically based on user input — ideal for enriching metadata, running Databricks queries, or augmenting Claude's capabilities.

---

# Server Setup Instructions
## 1. Verify Node.js is Installed (Required by MCP)

This project uses the Model Context Protocol (MCP) which requires Node.js under the hood — even for Python-based servers.

To check if Node is installed:
```bash
node --version
```
if not installed, download Node.js from https://nodejs.org and install it before continuing.

## 2. Clone this repository

```bash
git clone https://github.com/emma-mckee-pw/databricks-mcp-template
cd databricks-mcp-template
```

## 3. Python Environment Setup 
### Option A: Use ```uv``` (recommended)
Add this right after cloning:
```bash
# Create a virtual environment
uv venv

# Sync environment exactly to uv.lock
uv pip sync
```
If ```uv``` is not installed:
```bash
# Install uv if you don't already have it:
curl -Ls https://astral.sh/uv/install.sh | sh
```
Then retry the first commands in step 3

**Development Mode (editable install)**

After syncing:
```bash
uv pip install -e .
```
This installs the project in editable mode so that local changes are reflected without reinstalling.

To regenerate the uv.lock file (only when dependencies change):
```bash
# Recompile lockfile from pyproject.toml
uv pip compile --all-extras pyproject.toml

# Sync environment again
uv pip sync
```
You only need to do this if you update dependencies in pyproject.toml. Otherwise, uv pip sync is sufficient.

### Option B: Use traditional ```pip```
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```
## 4. Set up your environment
Copy the .env.example file:
```bash
cp .env.example .env
```
Open the .env file (nano, texteditor, etc) and add your databricks token:
```bash
open -a TextEdit .env
```
## 5. Start the MCP server
```bash
./start_server.sh
```

# Connect Claude Desktop to Server
You can also follow the official guide: https://modelcontextprotocol.io/quickstart/user for detailed generic instructions.
### 1. Open Claude Desktop Settings
  - MacOS: Click the Claude menu in your macOS top bar and select Settings
  - Windows: Right-click the Claude icon in your system tray (bottom right corner of your taskbar). Choose "Settings…" from the context menu.

(Note: This is not the in-app settings under your Claude user profile)

## 2. Enable Developer Mode
- In the left sidebar of the Settings window, click Developer
- Then click Edit Config
This opens the config file:
  - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
  - Windows: %APPDATA%\Claude\claude_desktop_config.json

If the file doesn’t exist, Claude will create it for you.

## 3. Configure MCP Server Connection
Replace the contents of the Claude Desktop config file with the structure provided in:
- claude_desktop_config.example.json in this repository

Then update file paths based on your operating system:

**On macOS:**
- Replace any path that looks like:
```
/Users/<your_username>/
```
- With your actual macOS username or full path.
Example:
```
/Users/emma/databricks-mcp-template/start_server.sh
```
**On Windows:**
- Replace the placeholder path with your Windows user directory, using either of the following:
```
C:/Users/your-username/databricks-mcp-template/start_server.sh
```
OR
```
C:\\Users\\your-username\\databricks-mcp-template\\start_server.sh
```
- Both slashes (/) and double backslashes (\\) are valid.

**Do not blindly overwrite your config. Always review the structure and file paths before saving, especially if you have other tools already configured.**

## 4. Restart Claude
After updating your configuration file, you need to restart Claude for Desktop.

Upon restarting, you should see a hammer icon in the bottom of the input box and a black lable indicating you are connected to Purplewave-data:

<img width="749" alt="image" src="https://github.com/user-attachments/assets/69d834cf-6c59-457e-9ce4-d1f624ae6f37" />

After clicking on the hammer icon, you should see the tools that come with the Filesystem MCP Server:

<img width="522" alt="image" src="https://github.com/user-attachments/assets/b58fdf0f-58af-44f0-b272-99c8565b6454" />

For troubleshooting assistance, see https://modelcontextprotocol.io/quickstart/user#troubleshooting

## 5. Test it out!
The project with the instruction prompt specific to this server is called Item Basics Assistant
- Navigate to project under "Projects" in the ribbon on the left hand side
- Select the Item Basics Assistant project space
- Try asking Claude a question about our Purple Wave Item Data! 

>>>>>>> c33488e (Update server functionality; Add chat context module; Update setup and install instructions)
