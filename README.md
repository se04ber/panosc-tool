# panosc-tool

Minimal MCP server with one read-only tool, `panosc_search`, which searches
public datasets in the [PaNOSC](https://www.panosc.eu/) federation.

## Run with ToolHive

Needs Docker and [ToolHive](https://github.com/stacklok/toolhive) (`thv`).
From this folder:

```bash
docker build -t panosc-tool:local .
thv run --name panosc --transport streamable-http --target-port 8000 \
  --permission-profile ./toolhive-permissions.json panosc-tool:local
thv list
```

`thv list` shows the MCP URL, for example `http://127.0.0.1:59025/mcp`.
The permission profile only allows `federated.panosc.ess.eu`.

## Use the hosted one

We also host it at `https://physicsllm-rdm.desy.de:8443/panosc/mcp`. Ask
us for the token, then let ToolHive proxy it:

```bash
thv secret setup
thv run https://physicsllm-rdm.desy.de:8443/panosc/mcp --name panosc \
  --remote-auth-bearer-token-file ./panosc-token
thv list
```

`thv secret setup` is needed once, because ToolHive keeps the token in its
own secret store. Choose `encrypted`.

## Connect a client

Either let ToolHive configure your client (Claude Code, Cursor, VS Code)

```bash
thv client setup
```

or add the URL from `thv list` by hand, for example in Claude Code

```bash
claude mcp add --transport http panosc http://127.0.0.1:59025/mcp
```

## Try it

Ask "search PaNOSC for tomography datasets". The tool takes `query` and an
optional `limit` (default 10, max 50) and returns a list of records:

```json
{
  "dataset_id": "10.16907/c4fdaf60-562b-4501-a314-a7c153d676ee",
  "title": "X-ray scattering tensor tomography data for a validation sample",
  "summary": "X-ray scattering tensor tomography (XSTT) facilitates ...",
  "doi": "10.16907/c4fdaf60-562b-4501-a314-a7c153d676ee",
  "keywords": [],
  "score": 0.9
}
```
