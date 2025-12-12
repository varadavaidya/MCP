from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import httpx
import json
import asyncio 
from bs4 import BeautifulSoup

load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

docs_urls = { #when LLM asks about context, it can go through these documents.
    "wikipedia":"https://simple.wikipedia.org/wiki/Politics_of_the_United_States",
    "associated-press":"https://apnews.com/politics",
    "nbc":"https://www.nbcnews.com/politics",
}

async def search_web(query : str) -> dict | None:
    payload = json.dumps({"q":query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(SERPER_URL, headers= headers, data = payload, timeout = 30.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}


async def fetch_url(url: str):       #to return entire text
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url,timeout = 30.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            return text
        except httpx.TimeoutException:
            return "timeout error"


@mcp.tool()        # this is the tool that the agent will be able to call
async def get_docs(query: str, library: str):
    """
    Search the answers for a given query and library. where library is corpus of info.
    Supports wikipedia, associated press, nbc.

    Args:
        query: The query to search for (e.g. "what are two political parties in USA")
        library: The library to search in (e.g. "wikipedia")

    Returns:
        Cleaned documentation text from one or more relevant pages.
        On hard failure, returns a DOCS_FETCH_FAILED message so the model
        can decide to fall back to web search.
    """

    if library not in docs_urls:
        raise ValueError(
            f"Library {library} not supported. Supported libraries are: "
            f"{', '.join(docs_urls.keys())}"
        )

    search_query = f"{query} site:{docs_urls[library]}"
    results = await search_web(search_query)

    if not results or "organic" not in results or not results["organic"]:
        return "DOCS_FETCH_FAILED: no search results found for your query."


    BLOCKED_PATTERNS = [
        "enable javascript and cookies to continue",
        "please enable cookies",
        "checking if the site connection is secure",
        "access denied",
    ]

    def looks_like_bad_page(text: str) -> bool:
        """Detect JS/cookie walls and trivial 'Redirecting…' pages."""
        lower = text.lower()
        if any(p in lower for p in BLOCKED_PATTERNS):
            return True

        stripped = " ".join(lower.split())
        if stripped.startswith("redirecting") and len(stripped) < 200:
            return True

        return False

    def extract_main_text(html: str) -> str:
        """Use BeautifulSoup to grab meaningful content and clean it."""
        soup = BeautifulSoup(html, "html.parser")

        main = soup.find("main") or soup.find("article") or soup.body or soup

        for tag in main(["script", "style", "nav", "header", "footer"]):
            tag.decompose()

        text = main.get_text(separator="\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        text = "\n".join(lines)

        max_chars = 4000
        if len(text) > max_chars:
            text = text[:max_chars] + " …[truncated]"
        return text

    #
    useful_chunks: list[str] = []
    last_error: str | None = None
    max_pages = 3  
    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        for result in results["organic"]:
            url = result.get("link")
            if not url:
                continue

            try:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text
                text = extract_main_text(html)

                if len(text) < 200:
                    continue

                if looks_like_bad_page(text):
                    continue

                useful_chunks.append(f"URL: {url}\n\n{text}")

                if len(useful_chunks) >= max_pages:
                    break

            except Exception as e:
                last_error = str(e)
                continue

    if not useful_chunks:
        if last_error:
            return (
                "DOCS_FETCH_FAILED: tried multiple documentation URLs but all failed "
                f"(last error: {last_error}). These sites may require JS/cookies or authentication."
            )
        return (
            "DOCS_FETCH_FAILED: tried multiple documentation URLs but they looked like "
            "redirect or JS-only pages with no usable content."
        )

    return "\n\n---\n\n".join(useful_chunks)


        
'''       
@mcp.tool()        # this is the tool that the agent will be able to call
async def get_docs(query: str , library: str):
    """
    Search the docs for a given query and library.
    supports langchain, openai, and llama-index.

    Args:
        query: The query to search for (e.g "Chroma DB")
        library: The library to search in (e.g  "langchain")
    
    Returns:
        The search results from the docs.
    """

    if library not in docs_urls:
        raise ValueError(f"Library {library} not supported. Supported libraries are: {', '.join(docs_urls.keys())}")

    search_query = f"{query} site:{docs_urls[library]}"
    results = await search_web(search_query)

    if not results or "organic" not in results:
        return "No results found."

    text = ""

    for result in results["organic"]:
        page_text = await fetch_url(result["link"])
        text += "\n\n---\n\n" + page_text
    return text

'''

if __name__ == "__main__":
    print("Starting MCP docs server on stdio...")
    mcp.run(transport="stdio")
