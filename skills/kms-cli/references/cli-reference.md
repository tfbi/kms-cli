# KMS CLI Reference

## Trae Usage

This skill is meant to run inside Trae on the company Windows computer. Copy the `kms-cli` skill folder into the Trae skill location used by that environment.

The skill does not bundle the CLI executable. Before using the skill in Trae, make sure one of these is true:

- The Go single-file executable `kms.exe` exists in the working directory.
- `kms.exe` is packaged separately and available on `PATH`.
- The current terminal can run `kms --help`.

When Trae asks for commands, prefer Windows PowerShell examples.

## Windows Usage

Windows PowerShell:

```powershell
.\kms.exe --help
.\kms.exe me
.\kms.exe kbs --page 1 --page-size 20
```

No Python, Go, or Node.js runtime is required on the company Windows computer.

## Config

Default config paths:

- Windows: `%USERPROFILE%\.kms\config.toml`
- macOS/Linux: `~/.kms/config.toml`

Example:

```toml
base_url = "https://internal.example.com"
token = "..."

[endpoints.me]
method = "GET"
path = "/api/me"

[endpoints.kbs]
method = "POST"
path = "/api/kbs"

[endpoints.channels]
method = "GET"
path = "/api/channels"

[endpoints.faqs]
method = "POST"
path = "/api/faqs"

[endpoints.faq_detail]
method = "GET"
path = "/api/faq/detail"
```

`KNOWLEDGE_TOKEN` takes priority over `token` in the config file.

PowerShell token example:

```powershell
$env:KNOWLEDGE_TOKEN = "paste-token-here"
```

## Commands

```bash
kms me
kms kbs --page 1 --page-size 20
kms channels <knowledgeId>
kms faqs <channelId> --page 1 --page-size 20
kms faq <faqId>
```

Add `--json` to any command for raw JSON output:

```bash
kms me --json
```

Use a custom config file:

```bash
kms --config ./config.toml me
```

## Request Mapping

| CLI command | HTTP method | Parameters sent |
| --- | --- | --- |
| `kms me` | GET | none |
| `kms kbs --page 1 --page-size 20` | POST | JSON body: `{"pageNo": 1, "pageSize": 20}` |
| `kms channels <knowledgeId>` | GET | query: `knowledgeId=<value>` |
| `kms faqs <channelId> --page 1 --page-size 20` | POST | JSON body: `{"channelId": "...", "pageNo": 1, "pageSize": 20}` |
| `kms faq <faqId>` | GET | query: `faqId=<value>` |

## Expected Behavior

- On HTTP `401` or `403`, the CLI asks the user to paste a new token and retries once.
- If the new token should be reused, the CLI can save it back to config after confirmation.
- Non-2xx responses, invalid JSON, and network failures should produce Chinese error messages.
