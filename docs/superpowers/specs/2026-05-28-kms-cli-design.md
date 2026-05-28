# KMS CLI Design

## Purpose

Build a lightweight Python CLI named `kms` for accessing an internal knowledge center. The knowledge center does not provide a public API, but the CLI will call known internal HTTP endpoints supplied by configuration.

The first version supports four commands:

- `kms me`: query the current user's information.
- `kms spaces`: list knowledge bases and their child channels that the current user can access.
- `kms faqs <channel_id>`: list FAQs under a specific channel.
- `kms faq <faq_id>`: show details for a specific FAQ.

## Scope

This project starts from an empty repository. The implementation should provide a small, maintainable Python package with a CLI entry point, request client, config loader, token handling, and focused tests.

Out of scope for the first version:

- Discovering or reverse engineering internal endpoints.
- Browser login automation.
- Multi-user profile management.
- Caching remote responses.
- Editing or publishing knowledge base content.

## Recommended Approach

Use a lightweight Python CLI with clear boundaries:

- CLI layer parses commands and formats output.
- Client layer owns HTTP requests and endpoint path expansion.
- Config layer loads base URL, endpoint paths, and optional token.
- Auth layer resolves the token and handles manual replacement when it expires.

This keeps the first version simple while leaving room to grow into a reusable SDK later.

## Configuration

The CLI reads configuration from `~/.kms/config.toml` by default.

Example:

```toml
base_url = "https://internal.example.com"
token = "..."

[paths]
me = "/api/me"
spaces = "/api/knowledge-bases"
faqs = "/api/channels/{channel_id}/faqs"
faq_detail = "/api/faqs/{faq_id}"
```

Configuration behavior:

- `base_url` is required.
- All four paths are required.
- `token` is optional because the environment variable can provide it.
- A future `--config` option may allow an alternate config path, but the first implementation can use the default path unless tests need injection.

## Token Resolution

Token priority:

1. `KNOWLEDGE_TOKEN` environment variable.
2. `token` from `~/.kms/config.toml`.
3. Interactive prompt if no token is available.

When a request fails because the token is expired or unauthorized, the CLI prompts the user to paste a new token. If the token came from the config file, or if no token was previously stored, the CLI asks whether to write the new token back to `~/.kms/config.toml`.

Expired-token detection should initially treat HTTP `401` and `403` as authentication failures. If the internal service has a specific JSON error code for token expiry, the client can add support for it behind the same auth failure path.

## HTTP Behavior

All requests go through a `KnowledgeClient`.

Client responsibilities:

- Join `base_url` and configured paths safely.
- Substitute path variables such as `{channel_id}` and `{faq_id}`.
- Send the token in the configured authentication header.
- Parse JSON responses.
- Raise typed errors for auth failures, network failures, invalid JSON, and non-success HTTP statuses.

The first design assumes bearer-token authentication:

```http
Authorization: Bearer <token>
```

If the real internal endpoint uses a different header, the config model should be extended with an `auth_header` or `auth_template` field before implementation.

## Output

Default output should be human-readable:

- `kms me`: print key user fields.
- `kms spaces`: show knowledge bases with indented child channels.
- `kms faqs <channel_id>`: show FAQ IDs and titles.
- `kms faq <faq_id>`: show the full FAQ detail in a readable structure.

All commands should also support `--json` to print the parsed JSON response without extra formatting. This makes the CLI useful in scripts and avoids losing fields the formatter does not know about.

## Error Handling

Expected errors:

- Missing config: explain where the config file should be created.
- Missing required config key: name the key.
- Missing token: prompt for one.
- Authentication failure: prompt for a replacement token and retry once.
- Network failure: show the base URL and the underlying connection error.
- Non-2xx response: show status code and a short response body preview.
- Invalid JSON: show that the endpoint returned an unexpected body.

The CLI should avoid printing token values in errors, logs, or tracebacks.

## Testing Strategy

Tests should cover:

- Config loading and required-key validation.
- Token priority between environment and config file.
- Path rendering for channel and FAQ commands.
- Auth failure retry with a manually supplied replacement token.
- CLI command dispatch and JSON output.
- Error messages for missing config and non-success responses.

HTTP tests should mock the transport rather than calling real internal services.

## Open Decisions

The design is otherwise ready, but implementation needs the real endpoint details:

- Exact `base_url`.
- Exact path templates.
- Exact auth header format if it is not `Authorization: Bearer <token>`.
- Response field names for the human-readable formatters.
