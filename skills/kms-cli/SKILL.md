---
name: kms-cli
description: 当 Trae、Codex 或类似编码环境里的 AI 助手需要使用、配置、说明、测试或排查内部知识中台 KMS CLI 时使用本技能，包括 Windows 单文件版 `kms.exe`、token/config.toml 配置、查询用户信息、通过 `kbs` 查询知识库、查询渠道、FAQ 列表、FAQ 详情，以及 `knowledgeId`、`channelId`、`faqId`、`pageNo`、`pageSize` 的请求参数映射。
---

# KMS CLI

## 概览

使用本地 `kms` CLI 访问公司内部知识中台。这个技能主要用于复制到公司 Windows 电脑的 Trae 环境中执行。除非用户明确要求其他语言，否则面向用户的说明尽量使用中文。

需要查看完整命令、配置和参数映射时，读取 [cli-reference.md](references/cli-reference.md)。

## 工作流程

1. 确认用户是要使用、配置、修改或排查 KMS CLI。
2. 先定位可执行命令：
   - 在 Windows 的 Trae 环境中使用 `.\kms.exe`，如果已经加入 `PATH`，也可以直接使用 `kms`。
   - 如果全局安装过，`kms` 也可能已经在 `PATH` 中。
3. 发起真实请求前先检查配置：
   - Windows 默认配置路径是 `%USERPROFILE%\.kms\config.toml`。
   - macOS/Linux 默认配置路径是 `~/.kms/config.toml`。
   - 不要打印或暴露 token 值。
4. 按用户需求运行最小必要命令：
   - `kms me`
   - `kms kbs`
   - `kms channels <knowledgeId>`
   - `kms faqs <channelId>`
   - `kms faq <faqId>`
5. 用户需要脚本处理或查看原始响应时，给命令追加 `--json`。
6. 如果请求返回认证失败，让 CLI 提示用户输入新 token，或建议设置 `KNOWLEDGE_TOKEN`。

## 关键规则

- CLI 分页参数保持命令行友好形式：`--page` 和 `--page-size`。
- 实际 HTTP 请求字段不同：发送 `pageNo`、`pageSize`、`knowledgeId`、`channelId`、`faqId`。
- 知识库和渠道是父子关系：一个知识库可以有多个渠道。
- `kbs` 是知识库命令。不要使用旧命令名 `knowledge-bases` 或 `spaces`。
- GET 请求使用普通 query 参数，不使用路径参数。
- POST 请求使用 JSON body。
- 这个技能只告诉 AI 助手如何使用 KMS CLI；公司电脑上仍然需要存在 `kms.exe` 和配置文件。

## 安全要求

- 不要编造内部接口路径。读取或询问 `config.toml` 中的真实配置。
- 不要记录 token，不要在最终回答里粘贴 token，也不要在示例里写真实 token。
- 如果用户询问分发方式，说明当前交付物是 Go 单文件版 `kms.exe`，目标机器不需要安装 Python、Go 或 Node.js。
