# KMS CLI

Python CLI for an internal knowledge center.

## Requirements

- Python 3.11 or newer
- Network access to the internal knowledge center
- A valid user authentication token

## Install On Windows

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

For development with tests:

```powershell
python -m pip install -e ".[dev]"
python -m pytest -v
```

## Install On macOS Or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

For development with tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest -v
```

## Config

Create the config file at:

- Windows: `%USERPROFILE%\.kms\config.toml`
- macOS/Linux: `~/.kms/config.toml`

Example:

```toml
base_url = "https://internal.example.com"
token = "..."

[endpoints.me]
method = "GET"
path = "/api/me"

[endpoints.spaces]
method = "POST"
path = "/api/knowledge-bases"

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

`KNOWLEDGE_TOKEN` overrides the token stored in the config file.

PowerShell example:

```powershell
$env:KNOWLEDGE_TOKEN = "paste-token-here"
```

## Commands

```bash
kms me
kms spaces --page 1 --page-size 20
kms channels <knowledge_base_id>
kms faqs <channel_id> --page 1 --page-size 20
kms faq <faq_id>
```

Add `--json` to any command to print raw JSON:

```bash
kms me --json
```

Use a custom config path:

```bash
kms --config ./config.toml me
```
