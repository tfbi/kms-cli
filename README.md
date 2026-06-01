# KMS CLI

用于访问内部知识中台的命令行工具。

公司 Windows 电脑上使用 Go 单文件版 `kms.exe`，无需安装额外运行时。

## 环境要求

- 能访问公司内部知识中台网络
- 一个有效的用户认证 token

## Windows 使用

PowerShell：

```powershell
.\kms.exe --help
.\kms.exe me
```

如果和 skill 一起分发，推荐直接使用 skill 目录里的包装脚本，不需要配置 PATH：

```powershell
.\skills\kms-cli\bin\kms.ps1 me --json
```

包装脚本会优先读取 `skills\kms-cli\config\config.toml`，并把 PowerShell 输出切到 UTF-8，减少中文乱码。真实配置可从 `skills\kms-cli\config\config.toml.example` 复制生成。

macOS / Linux / CentOS 使用：

```bash
./skills/kms-cli/bin/kms.sh me --json
```

`kms.sh` 会自动选择 macOS Apple Silicon 的 `kms-darwin-arm64` 或 Linux/CentOS x86_64 的 `kms-linux-amd64`。

配置文件仍然放在：

```text
%USERPROFILE%\.kms\config.toml
```

## 本地开发

```bash
go test ./...
```

## 配置文件

请创建配置文件：

- Windows: `%USERPROFILE%\.kms\config.toml`
- macOS/Linux: `~/.kms/config.toml`

配置示例：

```toml
base_url = "https://internal.example.com"
token = ""

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

token 读取顺序：

1. 环境变量 `KNOWLEDGE_TOKEN`
2. 配置文件里的 `token`
3. 手动输入

PowerShell 示例：

```powershell
$env:KNOWLEDGE_TOKEN = "在这里粘贴-token"
```

## 命令

```bash
kms me
kms kbs --page 1 --page-size 10
kms channels <knowledgeId>
kms faqs <channelId> --page 1 --page-size 10
kms faq <channelId> <faqId>
```

## 请求参数

CLI 会按以下字段名请求内部接口：

- 所有请求：HTTP header 固定传 `tenant-id: 2`
- 知识库列表：POST body 传 `pageNo`、`pageSize`
- 渠道列表：GET query 传 `knowledgeId`，并固定传 `type=1`、`authorityType=0`
- FAQ 列表：POST body 传 `channelId`、`categoryId`、`pageNo`、`pageSize`，其中 `categoryId` 和 `channelId` 值相同
- FAQ 详情：GET query 传 `channelId`、`faqId`

任意命令都可以追加 `--json` 输出原始 JSON：

```bash
kms me --json
```

使用自定义配置文件路径：

```bash
kms --config ./config.toml me
```
