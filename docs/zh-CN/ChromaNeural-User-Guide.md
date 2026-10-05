# ChromaNeural

[English](../en/ChromaNeural-User-Guide.md) · [Dansk](../da/ChromaNeural-User-Guide-DA.md) · [Deutsch](../de/ChromaNeural-User-Guide.md) · [Français](../fr/ChromaNeural-User-Guide.md) · [日本語](../ja/ChromaNeural-User-Guide.md) · [简体中文](ChromaNeural-User-Guide.md) · [हिन्दी](../hi-IN/ChromaNeural-User-Guide.md)
## 用户指南

ChromaNeural 0.2.21-rc.2 文档 | 未公开候选版本 | 2026年10月3日

**rc.2 文档状态：** 本候选版本尚未公开发布。本地化与可扩展 i18n 已通过本地验证；rc.2 原生构建和软件包验收仍待完成。以下安装、平台、LAN/WAN、推理及线上服务证据，除明确标为 rc.2 外，均属于历史 rc.1 证据。rc.1 下载不包含 rc.2 本地化。

## 1. 安装与启动

从官方 GitHub 发布下载对应平台包，将 SHA-256 与清单比较，并安装指南列出的运行前提。固定版本 ICP SDK 已包含，无需 npm 或旧开发环境。

Windows 从用户专属版本目录运行 Start-ChromaNeural.ps1。Linux 使用应用菜单或 chromaneural。macOS 安装前提后打开 ChromaNeural.app。包未签名，但不要为此全局禁用系统保护。

首次启动显示资源偏好，请选择并保存。保存不自动获得生产网络准入。示例中参与已停止，没有账户或私人数据。

![保存偏好后的概览，参与已停止。](../images/chroma-neural-overview.png)

保留的 rc.1 截图为丹麦语，不含 rc.2 语言选择器。**Oversigt** 是概览，**Ressourcer** 是资源，**Aktivitet** 是活动，**Login & forbindelse** 是登录与连接。步骤保留旧标签并附译文。除非明确另选，rc.2 以英语启动。

横线表示没有确认值，不是零余额或预计收益。使用左侧导航切换页面。

## rc.2 客户端语言

同一个客户端支持 English、Dansk、Deutsch、Français、日本語、简体中文和 हिन्दी。默认及回退语言均为英语，与操作系统语言无关。侧栏语言选择器会立即切换应用自身的文本，保留现有输入、源文本、连接 JSON 和参与状态；切换不会启动额外工作进程或网络探测。操作系统自带文件选择控件保持系统语言。

在 GUI 中明确选择语言后，仅将版本和语言标识保存到现有 `preferences.json` 旁的 `ui-language.json`。不会更改原设置架构或创建第二个状态根目录。下次启动恢复选择。缺失、无效、过大或不受支持的语言设置均回退英语，不改写原文件。之后明确保存时会保留无效原件；保存失败则保留当前语言。

可选 CLI 参数 `--language` 只覆盖本次启动，不保存。Windows 启动器传递 `-Language`。支持的标识来自 `client/locale-registry.json`，首批为 `en`、`da`、`de`、`fr`、`ja`、`zh-CN`、`hi-IN`。新增语言只需包含相同消息键的一个目录资源，以及含显示名称和数字格式元数据的一个注册项。验证用临时第八语言不随产品交付。

rc.2 客户端选择本指南语言时，对应标签如下：

| 历史截图标签 | rc.2 简体中文标签 |
|---|---|
| Oversigt | 概览 |
| Ressourcer | 资源 |
| Aktivitet | 活动 |
| Login & forbindelse | 登录与连接 |
| Udviklerværktøjer  ↗ | 开发者工具  ↗ |
| Afslut ChromaNeural | 退出 ChromaNeural |
| Gem ændringer | 保存更改 |
| Gem og fortsæt | 保存并继续 |
| Log ind med Internet Identity | 使用 Internet Identity 登录 |
| Gem forbindelsesdata | 保存连接数据 |
| Kontrollér forbindelse | 检查连接 |
| Backend svarer · offentligt API nået<br>Privat login er fortsat i browseren | 后端有响应 · 已访问公开 API<br>私有登录仍保留在浏览器中 |
| Lokal AI | 本地 AI |
| Privat II-lagring | 私有 II 存储 |

<!-- page -->
## 2. 资源与参与

![实际资源设置，此例未启用 CPU 贡献。](../images/chroma-neural-resources.png)

1. 打开 **Ressourcer**（资源）。
2. 选择最大推理线程数和内存偏好。
3. 选择是否仅空闲计算、是否电池供电时暂停。
4. 在支持的平台设置系统托盘行为。
5. 点击 **Gem ændringer**（保存更改），首次为 **Gem og fortsæt**（保存并继续）。通过 **Oversigt** 返回。

设置是上限而非硬件预留。已记录 Windows 内置 CPU 配置强制执行 CPU 调度、推理线程及提交内存限制，不保证总物理 RAM/RSS。受控 Ollama、Linux、macOS、GPU 贡献不支持，不能宣传为已强制限制的配置。

通用资源共享仍禁用。启动或暂停不绕过任务批准、节点准入和资源控制。仅安装或闲置硬件不会赚取积分。

<!-- page -->
## 3. 登录与连接

![未加载连接配置；浏览器登录与 API 检查独立。](../images/chroma-neural-connection.png)

1. 打开 **Login & forbindelse**（登录与连接）。
2. **Log ind med Internet Identity** 在浏览器打开现有 Web 应用。使用自己的现有身份，不分享会话或恢复资料。
3. 复制 Web 应用 API 配置，粘贴到客户端，点击 **Gem forbindelsesdata**（保存连接数据）。
4. **Kontrollér forbindelse**（检查连接）只检查公开 API，不传输私人浏览器会话。
5. 成功显示 **Backend svarer · offentligt API nået** 和 **Privat login er fortsat i browseren**，即后端响应、已访问公开 API、私人登录仍在浏览器。

该成功消息在历史 rc.1 Windows 验收中观察到，只证明公开 API 可达，不证明私人访问、节点准入或生产迁移。本文不要求部署或修改后端。

失败时检查互联网、所选配置和 Python/Node 前提。只分享脱敏错误说明；日志可能包含本地路径。不要首先重置身份或删除状态。

实际线上 II 端到端仍未验证。客户端发布不证明本地访问防护修复已部署到公开 Web 应用。

<!-- page -->
## 4. 活动、暂停与退出

![含真实本地保存设置事件的活动页。](../images/chroma-neural-activity.png)

活动显示客户端记录的事件，可帮助判断设置是否保存、操作产生什么状态。事件本身不证明 AI 质量已验证、已发布或已获积分。

支持的工作进程必须遵守暂停和停止。已批准本地任务在受控重启后保留队列身份。收到的节点内容必须保持惰性。

侧栏 **Afslut ChromaNeural**（退出 ChromaNeural）完全退出。托盘模式启用且受支持时，窗口关闭按钮可能只隐藏客户端。备份或移动状态前先退出。

<!-- page -->
## 5. 本地 AI 与高级操作

现有本地 AI 位于 **Udviklerværktøjer**（开发者工具）。打开或保存相关文本文件，选择 **Local AI**、支持的本地提供者／模型和指令，批准准确输入。接受和保存前审查提案；提案不会自动覆盖文件。

Windows/Linux 提供内置 CPU/Qwen。已安装本地 Ollama 模型需明确选择。macOS 无内置 Qwen。不会自动回退其他提供者。手动本地 AI 与网络受控资源配置独立。

本 RC 的队列／节点操作是高级 CLI 功能：queue-ai、result、task-question、task-accept、task-reply、task-collect、task-status。使用 --help 和明确选择的本地配置。它们不是自动线上入网通道。

## 6. 私人文件与结果

只在明确选择的文件夹工作。**Private II storage** 仅展示信息，不上传或下载私人文件。浏览器所有者数据和桌面文件尚无授权文件通道连接。

本地结果可作为提案审查。已批准节点回复即使 SHA-256 一致，也不自动成为已验证结果。全局发布仍需验证、共享同意、角色和后端接受。下载或审查不发放 ChromaPoints。

截图保留历史 rc.1。旧页脚 0.2.5 是内部组件标签，所述发行版为 0.2.21-rc.1。

MCP 仍是 rc.2 之后需要单独决策和验收的功能，此处尚未实现。本文档不代表新增生产环境或 Internet Identity 变更。
