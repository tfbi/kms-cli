---
name: kms-cli
description: Use when Codex needs to operate, configure, document, test, or troubleshoot the internal knowledge-platform KMS CLI, including the Python `kms` command, Windows installation, token/config.toml setup, querying user info, knowledge bases via `kbs`, channels, FAQ lists, FAQ details, and request parameter mapping for `knowledgeId`, `channelId`, `faqId`, `pageNo`, and `pageSize`.
---

# KMS CLI

## Overview

Use the local `kms` CLI to access the internal knowledge platform. Keep user-facing explanations in Chinese unless the user asks otherwise.

For exact command, config, and parameter details, read [cli-reference.md](references/cli-reference.md).

## Workflow

1. Confirm the user wants to use or modify the KMS CLI.
2. Locate the command:
   - In this repo, prefer `.venv/bin/kms` on macOS/Linux.
   - On Windows, expect `.\.venv\Scripts\kms.exe` after installation.
   - If installed globally, `kms` may be available on `PATH`.
3. Check configuration before real requests:
   - Default config is `~/.kms/config.toml` on macOS/Linux.
   - Default config is `%USERPROFILE%\.kms\config.toml` on Windows.
   - Never print or expose token values.
4. Run the narrowest command needed:
   - `kms me`
   - `kms kbs`
   - `kms channels <knowledgeId>`
   - `kms faqs <channelId>`
   - `kms faq <faqId>`
5. Use `--json` when the user wants scriptable output or raw response inspection.
6. If a request returns auth failure, let the CLI prompt for a new token or advise setting `KNOWLEDGE_TOKEN`.

## Important Details

- CLI pagination flags stay user-friendly: `--page` and `--page-size`.
- HTTP request fields are different: send `pageNo`, `pageSize`, `knowledgeId`, `channelId`, and `faqId`.
- Knowledge base and channel are parent-child entities: one knowledge base can have multiple channels.
- `kbs` is the knowledge-base command. Do not use old names such as `knowledge-bases` or `spaces`.
- GET requests use query parameters, not path parameters.
- POST requests use JSON bodies.

## Safety

- Do not invent internal endpoint paths. Read or ask for `config.toml` values.
- Do not log tokens, paste tokens into final answers, or include tokens in examples beyond placeholders.
- If the user asks about distribution, explain that Python requires a Python runtime unless packaged; Go is better for a single Windows `.exe`.
