---
name: kms-cli
description: 当 Trae、Codex 或类似编码环境里的 AI 助手需要使用、配置、说明、测试或排查公司内部知识中台 KMS CLI 时使用本技能，尤其是 Windows 单文件版 kms.exe、token/config.toml 配置、查询用户信息、知识库、渠道、FAQ 列表和 FAQ 详情。
---

# KMS CLI

## 概览

使用本地 `kms` CLI 访问公司内部知识中台。这个技能主要用于复制到公司 Windows 电脑的 Trae 环境中执行。除非用户明确要求其他语言，否则面向用户的说明尽量使用中文。

需要查看完整命令、配置和参数映射时，读取 [cli-reference.md](references/cli-reference.md)。

## 给 Trae 的强制规则

- 优先使用 skill 目录里的包装脚本，不要求用户配置 PATH。
- Windows / PowerShell 使用：`.\skills\kms-cli\bin\kms.ps1 ...`。
- Linux / CentOS / macOS shell 使用：`./skills/kms-cli/bin/kms.sh ...`。
- 不要猜接口路径，必须读取或让用户提供 `config.toml`。
- 不要输出真实 token，不要把 token 写进回答。
- token 优先来自环境变量 `KNOWLEDGE_TOKEN`；没有环境变量时，CLI 再读取配置文件里的 `token`；还没有时，CLI 会提示手动输入。
- 如果用户是让你“分析、总结、查找、提取答案”，运行命令时优先追加 `--json`，拿完整 JSON 给模型分析。
- 如果用户只是想人工查看列表，可以不加 `--json`，CLI 会输出简短列表。
- 不知道 `knowledgeId` 时，先运行 `kms kbs --json`。
- 不知道 `channelId` 时，先用 `knowledgeId` 运行 `kms channels <knowledgeId> --json`。
- 不知道 `faqId` 时，先用 `channelId` 运行 `kms faqs <channelId> --json`。
- 查 FAQ 详情必须同时传 `channelId` 和 `faqId`：`kms faq <channelId> <faqId> --json`。
- 遇到分页列表时，大模型必须根据用户目标和返回里的 `total`、`pageNum`、`pageNo`、`pageSize`、`dataList` 等字段自己判断是否继续翻页；不要只查第一页就说没有。

## 命令用途

| 命令 | 什么时候用 | 参数从哪里来 | 建议输出 |
| --- | --- | --- | --- |
| `kms me` | 查询当前 token 对应的用户信息，确认认证是否正常 | 不需要业务参数 | 人看可不加 `--json`，模型分析加 `--json` |
| `kms kbs` | 获取当前用户有权限的知识库列表 | 不需要业务参数，可加 `--page`、`--page-size` | 给模型用 `kms kbs --json` |
| `kms channels <knowledgeId>` | 获取某个知识库下面的渠道列表 | `knowledgeId` 来自 `kms kbs --json` 返回结果 | 给模型用 `kms channels <knowledgeId> --json` |
| `kms faqs <channelId>` | 获取某个渠道下面的 FAQ 列表 | `channelId` 来自 `kms channels <knowledgeId> --json` 返回结果 | 给模型用 `kms faqs <channelId> --json` |
| `kms faq <channelId> <faqId>` | 获取指定 FAQ 的完整详情 | `channelId` 来自渠道列表或 FAQ 列表上下文，`faqId` 来自 FAQ 列表 | 给模型用 `kms faq <channelId> <faqId> --json` |

## 推荐查询顺序

1. 先确认配置和认证：`kms me --json`。
2. 查询知识库：`kms kbs --json`，从返回结果里找 `knowledgeId`。
3. 查询渠道：`kms channels <knowledgeId> --json`，从返回结果里找 `channelId`。
4. 查询 FAQ 列表：`kms faqs <channelId> --json`，从返回结果里找 `faqId` 和 `title`。
5. 查询 FAQ 详情：`kms faq <channelId> <faqId> --json`，再基于完整 JSON 回答用户。
6. 如果当前页没有找到目标，但返回显示还有下一页，继续加 `--page <下一页>` 查询，直到找到目标或所有页查完。

## 工作流程

1. 确认用户是要使用、配置、修改或排查 KMS CLI。
2. 先定位可执行命令：
   - 在 Windows 的 Trae 环境中优先使用 `.\skills\kms-cli\bin\kms.ps1`。
   - 在 Linux / CentOS / macOS shell 中优先使用 `./skills/kms-cli/bin/kms.sh`。
   - 如果用户明确说已经加入 `PATH`，也可以直接使用 `kms`。
3. 发起真实请求前先检查配置：
   - skill 内置配置模板：`skills/kms-cli/config/config.toml.example`。
   - 推荐把模板复制为 `skills/kms-cli/config/config.toml`，包装脚本会自动使用它。
   - 如果没有 skill 目录下的配置文件，CLI 会回退到默认配置路径：Windows `%USERPROFILE%\.kms\config.toml`，macOS/Linux `~/.kms/config.toml`。
   - 不要打印或暴露 token 值。
4. 按用户需求运行最小必要命令。给 AI 分析时默认追加 `--json`：
   - `kms me`
   - `kms kbs`
   - `kms channels <knowledgeId>`
   - `kms faqs <channelId>`
   - `kms faq <channelId> <faqId>`
5. 用户需要脚本处理、模型分析、搜索答案或查看原始响应时，给命令追加 `--json`。
6. 如果请求返回认证失败，让 CLI 提示用户输入新 token，或建议设置 `KNOWLEDGE_TOKEN`。

## 关键规则

- CLI 分页参数保持命令行友好形式：`--page` 和 `--page-size`。
- 默认分页是第一页、每页 10 条；需要继续查询时由大模型自己计算下一页，例如 `--page 2 --page-size 10`。
- 实际 HTTP 请求字段不同：发送 `pageNo`、`pageSize`、`knowledgeId`、`channelId`、`categoryId`、`faqId`。
- 渠道列表请求固定追加查询参数：`type=1`、`authorityType=0`。
- FAQ 列表请求固定追加 body 参数：`categoryId`，值和 `channelId` 相同。
- FAQ 详情请求是 GET query，必须同时发送 `channelId` 和 `faqId`。
- 所有 HTTP 请求都固定携带请求头 `tenant-id: 2`。
- 知识库和渠道是父子关系：一个知识库可以有多个渠道。
- `kbs` 是知识库命令。不要使用旧命令名 `knowledge-bases` 或 `spaces`。
- GET 请求使用普通 query 参数，不使用路径参数。
- POST 请求使用 JSON body。
- 这个技能只告诉 AI 助手如何使用 KMS CLI；公司电脑上仍然需要存在 `kms.exe` 和配置文件。
- 禁止直接调用 KMS HTTP 接口；必须通过 `kms.exe`、`kms.ps1` 或 `kms.sh`。

## 安全要求

- 不要编造内部接口路径。读取或询问 `config.toml` 中的真实配置。
- 不要记录 token，不要在最终回答里粘贴 token，也不要在示例里写真实 token。
- 不要在回答里暴露 `config.toml` 中的真实 `base_url`、接口 path 或 token。
- 如果用户询问分发方式，说明当前交付物是 Go 单文件版 `kms.exe`，Windows 目标机器无需安装额外运行时。
