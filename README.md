.

📘 MCP Information Search Server

An MCP (Model Context Protocol) server that provides trusted information retrieval for LLMs such as Claude Desktop.
This server allows an AI model to fetch clean, readable text from curated sources:

Simple Wikipedia

Associated Press – Politics

NBC News – Politics

The tool performs real-time information search using Serper (Google Search API), filters results to the chosen domain using site:, fetches each page asynchronously with httpx, and extracts high-quality text using BeautifulSoup — removing ads, navigation bars, JavaScript error pages, redirect loops, and cookie walls.

The result is a reliable, noise-free information provider for agent workflows.


```

✨ Features
🔹 1. Three curated “knowledge libraries”

The MCP tool supports:

Library Name	Source URL	Use Case
wikipedia	simple.wikipedia.org/wiki/Politics_of_the_United_States	Neutral background information
associated-press	apnews.com/politics	Current political news
nbc	nbcnews.com/politics	U.S. political coverage
🔹 2. Intelligent Google Search filtering

The tool does:

site:<domain> <query>


ensuring results come specifically from the selected library’s domain.

🔹 3. JS/Cookie wall & redirect protection

The server automatically skips pages that contain:

“Enable JavaScript and cookies to continue”

“Checking if the site connection is secure”

Short “Redirecting…” pages

Block / Access Denied pages

This avoids low-quality output and prevents fallback behavior in Claude.

🔹 4. Clean, structured output

Only meaningful article text is returned:

Removes <script>, <style>, <nav>, <header>, <footer>

Extracts text from <main> or <article> when available

Collapses whitespace

Limits size to avoid overwhelming the model

Tags results with their source URL

🔹 5. Fully async

Uses:

httpx.AsyncClient for concurrency

Async Serper search

Async HTML fetch

🔹 6. Claude-ready MCP tool

Claude Desktop (or any MCP client) can run:

call get_docs
    query="What are two major political parties in the US?"
    library="wikipedia"


And receive a clean, reliable information summary.

📦 Installation
1. Clone the repository
git clone <your-repo-url>
cd <your-repo-folder>

2. Install dependencies

Using pip:

pip install -r requirements.txt


Required packages:

mcp-server
python-dotenv
httpx
beautifulsoup4

3. Add your Serper API key

Create a .env file:

SERPER_API_KEY=your_api_key_here


Sign up for a free key at:
https://serper.dev

🚀 Running the MCP Server

Run the server using Python:

python main.py


You should see:

Starting MCP docs server on stdio...


The server will now communicate over STDIO (required for Claude Desktop).



🧩 Claude Desktop Integration

Open your Claude Desktop configuration file:

macOS: ~/Library/Application Support/Claude/claude_desktop_config.json

Windows: %APPDATA%\Claude\claude_desktop_config.json

Add:

{
  "mcpServers": {
    "info-search": {
      "command": "python",
      "args": ["C:/path/to/your/main.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}


Restart Claude Desktop.
