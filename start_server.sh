#!/bin/bash

echo "➡️  Navigating to project folder..."
pwd

echo "🔒 Activating virtual environment..."
source .venv/bin/activate

echo "🧹 Cleaning up old ports..."
lsof -ti :6277 | xargs kill -9 2>/dev/null
lsof -ti :6274 | xargs kill -9 2>/dev/null

echo "🚀 Launching MCP server..."
.venv/bin/mcp dev databricks_mcp.py

