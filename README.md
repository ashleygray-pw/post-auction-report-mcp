# databricks-mcp-template

A local [Model Context Protocol (MCP)](https://modelcontext.org/) server designed to work with [Claude Desktop](https://www.anthropic.com/index/claude-desktop) or any other MCP-compatible LLM client. This server allows tools to be called dynamically based on user input — ideal for enriching metadata, running Databricks queries, or augmenting Claude's capabilities.

---

# Server Setup Instructions

## 1. Clone this repository

```bash
git clone https://github.com/emma-mckee-pw/databricks-mcp-template
cd databricks-mcp-template
```
## 2. Install dependencies
```bash
npm install
# You need Node.js (v18+) and npm. If not installed, run:
brew install node
```
## 3. Set up your environment
Copy the .env.example file:
```bash
cp .env.example .env
```
Open the .env file (nano, texteditor, etc) and add your databricks token:
```bash
open -a TextEdit .env
```
## 4. Start the MCP server
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

