# KMS CLI 参考说明

## Trae 使用场景

这个技能主要用于公司 Windows 电脑上的 Trae 环境。使用时，把 `kms-cli` 技能目录复制到 Trae 当前支持的技能目录中。

这个技能本身不包含 CLI 可执行文件。在 Trae 中使用前，请确认满足以下任意一种情况：

- Go 单文件版 `kms.exe` 已经放在当前工作目录。
- `kms.exe` 已经单独分发，并且所在目录已加入 `PATH`。
- 当前终端可以正常运行 `kms --help`。

当 Trae 需要给出命令示例时，优先使用 Windows PowerShell 写法。

## Windows 使用

PowerShell 示例：

```powershell
.\kms.exe --help
.\kms.exe me
.\kms.exe kbs --page 1 --page-size 10
```

公司 Windows 电脑不需要安装 Python、Go 或 Node.js。

## 配置文件

默认配置路径：

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

环境变量 `KNOWLEDGE_TOKEN` 的优先级高于配置文件中的 `token`。

PowerShell 设置 token 示例：

```powershell
$env:KNOWLEDGE_TOKEN = "在这里粘贴-token"
```

## 命令

```bash
kms me
kms kbs --page 1 --page-size 10
kms channels <knowledgeId>
kms faqs <channelId> --page 1 --page-size 10
kms faq <faqId>
```

任意命令都可以追加 `--json`，用于输出原始 JSON：

```bash
kms me --json
```

使用自定义配置文件：

```bash
kms --config ./config.toml me
```

## 请求参数映射

所有请求都会固定携带 HTTP header：`tenant-id: 2`。

| CLI 命令 | HTTP 方法 | 实际发送参数 |
| --- | --- | --- |
| `kms me` | GET | 不传业务参数 |
| `kms kbs --page 1 --page-size 10` | POST | JSON body: `{"pageNo": 1, "pageSize": 10}` |
| `kms channels <knowledgeId>` | GET | query: `knowledgeId=<value>` |
| `kms faqs <channelId> --page 1 --page-size 10` | POST | JSON body: `{"channelId": "...", "pageNo": 1, "pageSize": 10}` |
| `kms faq <faqId>` | GET | query: `faqId=<value>` |

## 预期行为

- HTTP `401` 或 `403` 会被视为认证失败，CLI 会提示用户输入新 token，并自动重试一次。
- 如果新 token 需要复用，CLI 会询问是否写回配置文件。
- 非 2xx 响应、非法 JSON、网络失败等情况会输出中文错误信息。
