# KMS CLI

用于访问内部知识中台的命令行工具。

推荐在公司 Windows 电脑上使用 Go 单文件版 `kms.exe`，不需要安装 Python、Go 或 Node.js。

## 环境要求

- 能访问公司内部知识中台网络
- 一个有效的用户认证 token

## Windows 使用 Go 单文件版

PowerShell：

```powershell
.\kms.exe --help
.\kms.exe me
```

配置文件仍然放在：

```text
%USERPROFILE%\.kms\config.toml
```

## Python 版安装

如果需要使用或开发 Python 版，再安装 Python 3.10 或更高版本。

Windows PowerShell：

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

macOS 或 Linux：

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

环境变量 `KNOWLEDGE_TOKEN` 的优先级高于配置文件里的 `token`。

PowerShell 示例：

```powershell
$env:KNOWLEDGE_TOKEN = "在这里粘贴-token"
```

## 命令

```bash
kms me
kms kbs --page 1 --page-size 20
kms channels <knowledgeId>
kms faqs <channelId> --page 1 --page-size 20
kms faq <faqId>
```

## 请求参数

CLI 会按以下字段名请求内部接口：

- 知识库列表：POST body 传 `pageNo`、`pageSize`
- 渠道列表：GET query 传 `knowledgeId`
- FAQ 列表：POST body 传 `channelId`、`pageNo`、`pageSize`
- FAQ 详情：GET query 传 `faqId`

任意命令都可以追加 `--json` 输出原始 JSON：

```bash
kms me --json
```

使用自定义配置文件路径：

```bash
kms --config ./config.toml me
```
