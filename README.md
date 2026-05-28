# KMS CLI

用于访问内部知识中台的 Python 命令行工具。

## 环境要求

- Python 3.11 或更高版本
- 能访问公司内部知识中台网络
- 一个有效的用户认证 token

## Windows 安装

PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

如果需要本地开发和运行测试：

```powershell
python -m pip install -e ".[dev]"
python -m pytest -v
```

## macOS 或 Linux 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

如果需要本地开发和运行测试：

```bash
python -m pip install -e ".[dev]"
python -m pytest -v
```

## 配置文件

请创建配置文件：

- Windows: `%USERPROFILE%\.kms\config.toml`
- macOS/Linux: `~/.kms/config.toml`

配置示例：

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

环境变量 `KNOWLEDGE_TOKEN` 的优先级高于配置文件里的 `token`。

PowerShell 示例：

```powershell
$env:KNOWLEDGE_TOKEN = "在这里粘贴-token"
```

## 命令

```bash
kms me
kms spaces --page 1 --page-size 20
kms channels <knowledge_base_id>
kms faqs <channel_id> --page 1 --page-size 20
kms faq <faq_id>
```

任意命令都可以追加 `--json` 输出原始 JSON：

```bash
kms me --json
```

使用自定义配置文件路径：

```bash
kms --config ./config.toml me
```
