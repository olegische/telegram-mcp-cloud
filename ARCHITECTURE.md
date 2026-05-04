# Architecture

This project is a cloud-oriented fork of the upstream Telegram MCP server. The
target is a Codex-compatible Telegram MCP service that supports both local stdio
usage and Streamable HTTP usage without tying Telegram client lifetime to module
imports or process startup.

The core rule is simple: MCP transport owns MCP session lifetime, and Telegram
clients are scoped to that MCP session.

## Goals

- Keep MCP tool implementations transport-neutral.
- Support `stdio` and `streamable-http` with the same tool surface.
- Avoid import-time network, session, or Telegram client side effects.
- Make future SaaS authentication and per-user Telegram login possible without
  rewriting tools again.
- Keep local single-user usage working while moving toward session-scoped state.

## Non-Goals

- No service-level authentication in the first Streamable HTTP version.
- No bearer-token shortcut for the first version.
- No SaaS login flow until transport and session lifecycle are clean.
- No hand-rolled MCP Streamable HTTP protocol implementation while the official
  `mcp` package provides it.

## Current Problems

The current upstream-shaped implementation creates global Telegram clients in
`telegram_mcp.runtime` during import:

- environment variables are read at import time;
- `TelegramClient` instances are created at import time;
- tools call a global `get_client()`;
- `runner.py` starts all clients before starting stdio transport.

That model works for a local stdio process, but it is wrong for Streamable HTTP
and future SaaS behavior. HTTP clients create independent MCP sessions; those
sessions need isolated runtime state.

## Core Entities

### `ServiceConfig`

Process-level service configuration.

Examples:

- transport: `stdio` or `streamable-http`;
- HTTP host, port, and MCP path;
- logging level;
- Telegram account configuration source.

This object must not contain live Telegram clients.

### `TelegramAccountConfig`

Declarative configuration for one Telegram account.

Examples:

- account label;
- `TELEGRAM_API_ID`;
- `TELEGRAM_API_HASH`;
- session source: session string or session file name;
- optional proxy settings.

This object must be safe to create during app startup because it does not open a
Telegram connection.

### `TelegramClientManager`

Owns live `Telethon` clients for one MCP session.

Responsibilities:

- lazily build clients from `TelegramAccountConfig`;
- start clients when the MCP session needs Telegram access;
- warm entity caches if needed;
- reconnect and verify connectivity;
- close all clients when the MCP session ends.

No module outside this manager should instantiate `TelegramClient` directly.

### `McpSessionState`

Per-MCP-session runtime state.

Responsibilities:

- hold one `TelegramClientManager`;
- expose client resolution to tools;
- own cleanup for the session.

Required lifecycle:

- `stdio`: one `McpSessionState` per process;
- `streamable-http`: one `McpSessionState` per MCP session.

This distinction is intentional and must be preserved.

### `ClientResolver`

Small boundary used by tools to obtain a Telegram client.

Tools should depend on a resolver function or context-aware helper, not on a
global `clients` dictionary. This keeps tools transport-neutral and lets SaaS
auth later change where account configs come from.

## Transport Model

### stdio

`stdio` is a single local MCP session bound to one process.

Lifecycle:

1. build `ServiceConfig`;
2. build account configs;
3. create one `McpSessionState`;
4. run `mcp.run_stdio_async()`;
5. close the session state when the process exits.

### Streamable HTTP

Streamable HTTP uses the official `mcp` package implementation:

- `FastMCP.streamable_http_app()`;
- `FastMCP.run_streamable_http_async()`;
- default MCP endpoint path: `/mcp`.

Do not implement the JSON-RPC/SSE/session protocol by hand.

Lifecycle:

1. build `ServiceConfig`;
2. build account config source;
3. create the FastMCP app without live Telegram clients;
4. for each MCP HTTP session, create one `McpSessionState`;
5. tools resolve Telegram clients from that session state;
6. when the MCP session ends, close its Telegram clients.

Initial HTTP service must bind to localhost by default. Until service-level
authentication exists, exposing this server publicly is unsafe.

## Authentication

There is currently no service-level authentication in this fork.

Existing authentication is only Telegram authentication:

- session strings;
- file-based `.session` files;
- Telegram 2FA during session generation.

The first Streamable HTTP implementation should not add bearer token auth. That
would create an auth surface that will likely be replaced by real SaaS login.
Instead, keep the server unauthenticated and local-only by default.

Future SaaS auth should introduce:

- service user identity;
- tenant or workspace identity;
- encrypted storage for Telegram account configs;
- `McpSessionState` built from authenticated user context.

## Tool Rules

Tools must remain transport-neutral.

Allowed:

- ask for `Context` where MCP client features are needed;
- call a session-aware client resolver;
- accept an optional Telegram account label for multi-account selection.

Forbidden:

- creating `TelegramClient` in tool modules;
- reading process env in tool modules;
- importing a global live `clients` dictionary;
- starting or disconnecting Telegram clients from individual tools except
  through the manager.

## Refactoring Order

1. Introduce configuration objects without changing behavior.
2. Introduce `TelegramClientManager` and move client creation into it.
3. Introduce `McpSessionState`.
4. Replace global `clients` access with a session-aware resolver.
5. Keep stdio working through one process-scoped session state.
6. Add Streamable HTTP using official FastMCP transport.
7. Add tests for stdio process state and HTTP per-session state.
8. Only after that, design SaaS login/auth.

Do not add Streamable HTTP on top of the current global `clients` model. That
would make the service appear compatible while preserving the wrong lifecycle.

## Dependency Baseline

The project targets the official Python MCP package:

```toml
mcp>=1.27,<1.28
```

The `cli` extra is intentionally not required for service runtime.

## Security Notes

- `secrets/`, `.env`, `*.session`, and logs must remain ignored.
- Session strings grant Telegram account access and must never be committed.
- Until service auth exists, Streamable HTTP must be treated as a local-only
  endpoint.
- Sanitization of Telegram user-controlled content remains mandatory.
