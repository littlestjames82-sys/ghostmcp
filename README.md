# GhostMCP
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Ghost-native MCP (Model Context Protocol) **client** for Ghost
Developer Studio. GhostIDE shells out to GhostMCP to talk to MCP
servers from a standard MCP config file — the `.mcp.json` shape
used across the ecosystem — listing servers, listing a server's
tools, and calling a tool, in pure Python stdlib so it runs
anywhere GhostIDE runs, including on-device in the phone APK.

MIT licensed. Dependencies: none. Protocol version
`2024-11-05`; client info `{"name": "ghostmcp", "version":
"0.1.0"}`. JSON-RPC 2.0 throughout.

## Usage

```
python -m ghostmcp servers --config <path>
python -m ghostmcp tools --config <path> --server <name> [--timeout N]
python -m ghostmcp call --config <path> --server <name> --tool <name> --args '<json object>' [--timeout N]
```

Every verb prints ONE JSON object to stdout. `--timeout` is in
seconds, covers the whole invocation, and defaults to 30.

### servers

Lists the config's servers **without connecting to anything**:

```json
{"config": "mcp.json", "servers": [
  {"name": "files", "transport": "stdio",
   "target": "python3 server.py --root /tmp",
   "env_names": ["API_KEY"]},
  {"name": "remote", "transport": "http",
   "target": "https://example.com/mcp", "env_names": []}]}
```

`target` is the command and args joined for a stdio server, or
the url for an HTTP server. `env_names` carries env **names
only** — see Security below.

### tools

Connects, handshakes, and lists the server's tools
(`tools/list`, following `nextCursor` pagination):

```json
{"server": "files", "tools": [
  {"name": "read_file", "description": "Read a file.",
   "inputSchema": {"type": "object",
                   "properties": {"path": {"type": "string"}}}}]}
```

### call

Calls one tool and flattens its content: text blocks joined
with newlines, non-text blocks summarized as `[type: ...]`,
capped at 60,000 characters:

```json
{"server": "files", "tool": "read_file", "isError": false,
 "text": "the file's text"}
```

### Errors

Every failure prints `{"error": "..."}` to stdout and exits 2:
a missing or invalid config file, an unknown server name, bad
`--args` JSON, a server process that cannot start or dies
mid-session, a JSON-RPC error reply, an HTTP error status, and
timeouts.

One thing is deliberately **not** an error: a tool result the
server marked `isError: true`. That is the tool's own answer,
so it prints normally with `"isError": true` and exit 0.

## Config format

The standard MCP client config:

```json
{"mcpServers": {
  "files": {"command": "python3", "args": ["server.py"],
            "env": {"API_KEY": "..."}},
  "remote": {"url": "https://example.com/mcp"}}}
```

An entry with a `url` is an HTTP server; an entry with a
`command` is a stdio server. An entry with neither is an error.

## Transports

**Stdio.** The server is spawned as a child process per
invocation; JSON-RPC messages travel newline-delimited over its
stdin/stdout. The client sends `initialize`, then the
`notifications/initialized` notification, then the request. A
background reader matches replies by id; stray non-JSON lines
and server notifications are ignored, `ping` is answered, and
other server-initiated requests get a JSON-RPC method-not-found
reply. The child's stderr is drained and discarded so a chatty
server cannot deadlock on a full pipe. The child is **always**
terminated when the invocation ends — success, error, or
timeout.

**HTTP.** Each JSON-RPC message is a POST to the server `url`
(Streamable HTTP style). If a response carries an
`Mcp-Session-Id` header, the client sends it on every later
request in the same invocation. Bodies are accepted as plain
`application/json` or as `text/event-stream` (the reply is the
`data:` message whose id matches the request). A notification
such as `notifications/initialized` is posted and its (usually
empty, 202) reply ignored.

## Design: fresh session per call, and its limit

There is no daemon and no connection pool: each CLI invocation
opens a brand-new session, does one listing or one call, and
tears everything down. That makes every invocation independent
and crash-proof — a hung or hostile server can cost at most one
timeout — and it is what lets the same binary serve the desktop
server and the phone.

The limit follows directly: **a server that keeps state across
calls inside its own process will not keep it.** Anything held
in the server's memory (an in-memory cache, a half-finished
multi-call workflow, a stdio session's working set) resets on
every call. Servers that keep state in files, in a database, or
behind an HTTP session the server itself persists are
unaffected; servers designed around one long-lived stdio
conversation are a poor fit, and 0.1.0 is honest about that
rather than pretending otherwise.

## Security

- Env **values** from the config are passed to stdio server
  processes (that is what they are for) but are never printed,
  returned, or logged anywhere by GhostMCP. The `servers` verb
  reports env names only, and error messages never quote config
  contents or a server's stderr.
- Tool `--args` are passed to the server and nowhere else; they
  are never logged.
- A config is a program launcher: a stdio entry runs its
  `command` with the invoking user's privileges. Only point
  GhostMCP at configs you trust, exactly as with any MCP host.

## Scope of 0.1.0 — honestly

GhostMCP implements the client basics: `initialize`,
`tools/list`, `tools/call`, over stdio and HTTP. It does **not**
implement OAuth or any auth flow, sampling or elicitation
(server-initiated requests beyond `ping` are refused), the
resources or prompts verbs, tool-list change notifications, or
long-lived sessions. Those land only if a real GhostIDE need
pulls them in.

---
<!-- ghost-studio-footer -->
## More from Ghost Developer Studio

Ghost Developer Studio builds developer tools, AI-agent safety software, and practical apps, and sells by showing working software, not slide decks.

- [Roadmap board](https://github.com/littlestjames82-sys/ghost-roadmaps): where every studio product stands
- [Agent Seatbelt](https://github.com/littlestjames82-sys/agent-seatbelt): deterministic guardrails for AI coding agents
- [Ghost Hands](https://github.com/littlestjames82-sys/ghost-hands): governed, recorded, replayable agent hands
- [GhostSlice](https://github.com/littlestjames82-sys/ghostslice): agent context and prompt optimizer
- [GhostIDE](https://github.com/littlestjames82-sys/ghostide-android): fully offline AI code editor for Android
- [All studio projects](https://github.com/littlestjames82-sys?tab=repositories)
