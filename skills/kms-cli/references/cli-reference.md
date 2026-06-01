# KMS CLI 参考说明

## Trae 使用场景

这个技能主要用于公司 Windows 电脑上的 Trae 环境。使用时，把 `kms-cli` 技能目录复制到 Trae 当前支持的技能目录中。

这个技能本身不包含 CLI 可执行文件。在 Trae 中使用前，请确认满足以下任意一种情况：

- Go 单文件版 `kms.exe` 已经放在 `skills/kms-cli/bin/`。
- `kms.exe` 已经单独分发，并且所在目录已加入 `PATH`。
- 当前终端可以正常运行 `kms --help`。

当 Trae 需要给出命令示例时，优先使用 Windows PowerShell 写法。

## Skill 内置目录

```text
skills/kms-cli/
  bin/
    kms.exe              # Windows 可执行文件
    kms.ps1              # Windows PowerShell 包装脚本
    kms.sh               # Linux/CentOS/macOS shell 包装脚本
    kms-linux-amd64      # Linux/CentOS 可执行文件，编译后放这里
  config/
    config.toml.example  # 配置模板
    config.toml          # 真实配置，本文件不要提交
```

优先让 Trae 调用包装脚本：

```powershell
.\skills\kms-cli\bin\kms.ps1 me --json
```

Windows 下不要直接调用 `kms.exe`。`kms.ps1` 会在执行前把 PowerShell 输出编码和控制台代码页切到 UTF-8，减少 Trae 沙箱里中文响应乱码。

Linux / CentOS 示例：

```bash
./skills/kms-cli/bin/kms.sh me --json
```

包装脚本会优先使用 `skills/kms-cli/config/config.toml`。如果这个文件不存在，CLI 会使用系统默认配置路径。

## Windows 使用

PowerShell 示例：

```powershell
.\skills\kms-cli\bin\kms.ps1 --help
.\skills\kms-cli\bin\kms.ps1 me --json
.\skills\kms-cli\bin\kms.ps1 kbs --page 1 --page-size 10 --json
```

公司 Windows 电脑无需安装额外运行时。

## 配置文件

默认配置路径：

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

环境变量 `KNOWLEDGE_TOKEN` 的优先级高于配置文件中的 `token`。

token 读取顺序：

1. 先读环境变量 `KNOWLEDGE_TOKEN`。
2. 环境变量没有时，读取配置文件里的 `token`。
3. 配置文件也没有时，CLI 提示手动输入。

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
kms faq <channelId> <faqId>
```

任意命令都可以追加 `--json`，用于输出原始 JSON。Trae 或其他大模型需要分析、总结、提取答案时，优先使用 `--json`：

```bash
kms me --json
kms kbs --json
kms channels <knowledgeId> --json
kms faqs <channelId> --json
kms faq <channelId> <faqId> --json
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
| `kms channels <knowledgeId>` | GET | query: `knowledgeId=<value>&type=1&authorityType=0` |
| `kms faqs <channelId> --page 1 --page-size 10` | POST | JSON body: `{"channelId": "...", "categoryId": "...", "pageNo": 1, "pageSize": 10}`，其中 `categoryId` 和 `channelId` 值相同 |
| `kms faq <channelId> <faqId>` | GET | query: `channelId=<value>&faqId=<value>` |

## 每个命令具体做什么

| 命令 | 作用 | 下一步通常做什么 |
| --- | --- | --- |
| `kms me --json` | 查询当前 token 对应的用户信息，也可以用来验证 token 是否可用 | 如果认证失败，按 CLI 提示输入新 token |
| `kms kbs --json` | 获取当前用户有权限访问的知识库列表 | 从返回 JSON 中选择 `knowledgeId` |
| `kms channels <knowledgeId> --json` | 获取指定知识库下的渠道列表 | 从返回 JSON 中选择 `channelId` |
| `kms faqs <channelId> --json` | 获取指定渠道下的 FAQ 列表 | 从返回 JSON 中选择 `faqId`，同时保留当前 `channelId` |
| `kms faq <channelId> <faqId> --json` | 获取指定 FAQ 的详情 | 基于完整 JSON 回答用户问题 |

## 分页规则

- `kms kbs` 和 `kms faqs` 都支持 `--page`、`--page-size`。
- 不传分页参数时，默认查询第一页、每页 10 条。
- 大模型需要根据返回 JSON 自己判断是否继续翻页，常见字段包括 `total`、`pageNum`、`pageNo`、`pageSize`、`dataList`。
- 如果用户要查找某个 FAQ、某类问题或某个关键词，第一页没找到时，不要直接回答“没有”；先根据 `total` 和 `pageSize` 计算是否还有下一页。
- 下一页示例：`kms faqs <channelId> --page 2 --page-size 10 --json`。
- 当已经查完所有页，仍然没有命中，再告诉用户没有找到匹配内容。

## 给 Trae 的使用提醒

- 不要直接猜 `knowledgeId`、`channelId`、`faqId`，这些 ID 必须来自上一步命令返回。
- 如果用户问“某个问题怎么处理”，优先查 FAQ 列表，再查命中的 FAQ 详情。
- 如果用户没有给出明确知识库或渠道，先从 `kms kbs --json` 和 `kms channels <knowledgeId> --json` 开始缩小范围。
- 给模型分析时使用 `--json`，不要只依赖普通列表输出。

## 预期行为

- HTTP `401` 或 `403` 会被视为认证失败，CLI 会提示用户输入新 token，并自动重试一次。
- 如果新 token 需要复用，CLI 会询问是否写回配置文件。
- 非 2xx 响应、非法 JSON、网络失败等情况会输出中文错误信息。
