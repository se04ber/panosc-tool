import json

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

import panosc_tool


def fake_panosc(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    client = httpx.AsyncClient(base_url="https://panosc.test", transport=httpx.MockTransport(handler))
    monkeypatch.setattr(panosc_tool, "http", client)


async def test_search_sends_filter_and_maps_result(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET" and request.url.path == "/api/documents"
        assert json.loads(request.url.params["filter"]) == {"query": "tomography", "limit": 50}
        return httpx.Response(200, json=[{"pid": "p1", "title": "Bone", "score": 0.9}])

    fake_panosc(monkeypatch, handler)
    hits = await panosc_tool.panosc_search(" tomography ", 1000)
    assert hits == [
        {"dataset_id": "p1", "title": "Bone", "summary": "", "doi": "", "keywords": [], "score": 0.9}
    ]


@pytest.mark.parametrize("status", [None, 502])
async def test_bad_input_and_upstream_errors_are_tool_errors(
    monkeypatch: pytest.MonkeyPatch, status: int | None
) -> None:
    fake_panosc(monkeypatch, lambda request: httpx.Response(status or 200, json=[]))
    with pytest.raises(ToolError):
        await panosc_tool.panosc_search(" " if status is None else "x")


async def test_exposes_one_read_only_tool() -> None:
    tools = await panosc_tool.mcp.list_tools()
    assert [tool.name for tool in tools] == ["panosc_search"]
    assert tools[0].annotations.read_only_hint is True
