"""Minimal MCP server with one read-only tool: PaNOSC dataset search."""

import json
import os
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations

mcp = MCPServer(name="panosc-tool", version="0.1.0")
http = httpx.AsyncClient(
    base_url=os.getenv("PANOSC_BASE_URL", "https://federated.panosc.ess.eu"),
    # The federated search waits on every facility. 10 to 12 s is normal.
    timeout=30,
    follow_redirects=False,
)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True))
async def panosc_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search public datasets across PaNOSC facilities (ESS, ILL, PSI, ...).

    Use short keywords such as techniques, samples or instruments.
    Returns at most 50 records.
    """
    query = query.strip()
    if not query or len(query) > 500:
        raise ToolError("query must be 1 to 500 characters")
    limit = max(1, min(limit, 50))
    # PaNOSC's API is LoopBack-style: the text query goes inside `filter`.
    params = {"filter": json.dumps({"query": query, "limit": limit})}
    try:
        response = await http.get("/api/documents", params=params)
        response.raise_for_status()
        docs = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ToolError("PaNOSC is unavailable or returned an error") from exc
    return [
        {
            "dataset_id": doc.get("pid", ""),
            "title": doc.get("title", ""),
            "summary": doc.get("summary", ""),
            "doi": doc.get("doi", ""),
            "keywords": doc.get("keywords", []),
            "score": doc.get("score"),
        }
        for doc in (docs if isinstance(docs, list) else [])[:limit]
    ]


def main() -> None:
    # ToolHive sets MCP_TRANSPORT and MCP_PORT. Bind 0.0.0.0, not its MCP_HOST,
    # which is the proxy's target address and unreachable inside the container.
    if os.getenv("MCP_TRANSPORT") == "stdio":
        mcp.run("stdio")
        return
    mcp.run(
        "streamable-http",
        host="0.0.0.0",  # noqa: S104 - container listener
        port=int(os.getenv("MCP_PORT", "8000")),
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
