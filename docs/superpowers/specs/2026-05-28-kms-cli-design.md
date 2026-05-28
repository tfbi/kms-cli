# KMS CLI 设计文档

## 目标

开发一个轻量级 Python CLI，命令名为 `kms`，用于访问内部知识中台。知识中台目前没有开放 API，但 CLI 会请求已经确认过的内部 HTTP 接口；接口地址、路径和 token 通过配置提供。

第一版提供 5 个命令：

- `kms me`：查询当前用户信息。
- `kms kbs`：分页获取当前用户有权限访问的知识库列表。
- `kms channels <knowledge_base_id>`：获取指定知识库下的渠道列表。知识库和渠道是父子关系，一个知识库下可以有多个渠道。
- `kms faqs <channel_id>`：分页获取指定渠道下的 FAQ 列表。
- `kms faq <faq_id>`：获取指定 FAQ 的详情。

## 范围

当前仓库是一个空仓库，因此第一版会从零创建一个小型、可维护的 Python 包，包含 CLI 入口、HTTP 请求客户端、配置读取、token 处理和基础测试。

第一版不做这些事情：

- 自动发现或逆向分析内部接口。
- 自动化浏览器登录。
- 多用户配置档案管理。
- 远程数据缓存。
- 编辑、发布或管理知识库内容。

## 推荐方案

采用“轻量 CLI + 清晰分层”的实现方式：

- CLI 层：解析命令参数，并负责输出格式。
- Client 层：统一处理 HTTP 请求、接口路径拼接、query 参数和 POST body。
- Config 层：读取 `base_url`、接口路径和可选 token。
- Auth 层：解析 token 来源，并在 token 过期时支持手动替换。

这个方案足够简单，适合第一版快速落地；同时又保留了清晰边界，后续如果要扩展成可复用的 Python SDK，也不需要推倒重来。

## 配置文件

CLI 默认读取 `~/.kms/config.toml`。

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

配置规则：

- `base_url` 必填。
- 5 个接口配置都必填，每个接口配置包含 `method` 和 `path`。
- `token` 可选，因为 token 也可以通过环境变量提供。
- 后续可以增加 `--config` 参数支持自定义配置文件路径；第一版可以先使用默认路径，测试中再通过内部参数注入临时配置路径。

## Token 读取顺序

token 按以下优先级读取：

1. 环境变量 `KNOWLEDGE_TOKEN`。
2. `~/.kms/config.toml` 里的 `token`。
3. 如果前两者都没有，则交互式提示用户输入 token。

当请求因为 token 过期或无权限失败时，CLI 会提示用户粘贴一个新的 token。新 token 输入后，CLI 会重试当前请求一次。

如果原 token 来自配置文件，或者之前配置文件里没有 token，CLI 会询问是否把新 token 写回 `~/.kms/config.toml`，方便下次继续使用。

第一版先把 HTTP `401` 和 `403` 视为认证失败。如果内部服务有明确的 JSON 错误码表示 token 过期，后续可以把这个错误码接入同一套认证失败处理逻辑。

## HTTP 请求行为

所有请求都通过 `KnowledgeClient` 发出。

`KnowledgeClient` 负责：

- 安全拼接 `base_url` 和接口路径。
- 根据接口配置选择 `GET` 或 `POST`。
- 对 `GET` 请求使用普通 query 参数，不使用路径参数。例如渠道列表传 `knowledge_base_id`，FAQ 详情传 `faq_id`。
- 对 `POST` 请求使用 JSON body 传参。
- 在请求头里带上 token。
- 解析 JSON 响应。
- 对认证失败、网络失败、非法 JSON、非成功 HTTP 状态码抛出明确的错误类型。

接口请求规则：

- 查询用户信息：`GET` 请求，第一版默认不传业务参数。
- 获取知识库列表：`POST` 请求，body 里传分页参数。
- 获取渠道列表：`GET` 请求，query 参数传知识库 ID。
- 获取 FAQ 列表：`POST` 请求，body 里传分页参数和渠道 ID。
- 获取 FAQ 详情：`GET` 请求，query 参数传 FAQ ID。

第一版默认使用 Bearer Token：

```http
Authorization: Bearer <token>
```

如果实际内部接口使用其他请求头格式，需要在实现前扩展配置模型，例如增加 `auth_header` 或 `auth_template` 字段。

## 输出格式

默认输出为适合人阅读的文本：

- `kms me`：打印主要用户字段。
- `kms kbs`：展示知识库 ID、名称等摘要字段。
- `kms channels <knowledge_base_id>`：展示指定知识库下的渠道 ID、名称等摘要字段。
- `kms faqs <channel_id>`：展示 FAQ ID 和标题。
- `kms faq <faq_id>`：展示完整 FAQ 详情，格式保持清晰易读。

所有命令都支持 `--json`，用于输出解析后的原始 JSON 数据，不额外格式化。这样既方便脚本处理，也可以避免默认文本格式遗漏接口返回字段。

## 错误处理

需要处理的错误场景：

- 配置文件缺失：提示用户应该创建哪个配置文件。
- 必填配置项缺失：明确指出缺少哪个配置项。
- token 缺失：提示用户手动输入。
- 认证失败：提示用户输入新 token，并自动重试一次。
- 网络失败：展示 `base_url` 和底层连接错误。
- 非 2xx 响应：展示 HTTP 状态码和一小段响应内容。
- 返回内容不是合法 JSON：提示接口返回了非预期内容。

CLI 不应该在错误信息、日志或异常堆栈中打印 token。

## 测试策略

测试需要覆盖：

- 配置文件读取和必填字段校验。
- 环境变量 token 与配置文件 token 的优先级。
- `GET` 请求使用 query 参数传递知识库 ID 和 FAQ ID。
- `POST` 请求使用 JSON body 传递分页参数，以及 FAQ 列表所需的渠道 ID。
- 认证失败后，手动输入新 token 并重试。
- CLI 命令分发和 `--json` 输出。
- 配置缺失、非成功响应等错误信息。

HTTP 测试应使用 mock transport，不请求真实内部服务。

## 实现前需要确认的信息

设计本身已经可以进入实现阶段，但真正接入内部服务时还需要填入这些信息：

- 真实的 `base_url`。
- 真实的 5 个接口路径。
- 分页参数的真实字段名，例如 `page` / `page_size` 或 `pageNo` / `pageSize`。
- 知识库 ID、渠道 ID、FAQ ID 的真实参数名。
- 如果不是 `Authorization: Bearer <token>`，需要确认真实认证请求头格式。
- 用于默认文本输出的响应字段名，例如用户名称、知识库名称、渠道名称、FAQ 标题等。
