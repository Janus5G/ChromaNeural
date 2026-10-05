# ChromaNeural

[English](../en/ChromaNeural-Verified-Capabilities.md) · [Dansk](../da/ChromaNeural-Verified-Capabilities-DA.md) · [Deutsch](../de/ChromaNeural-Verified-Capabilities.md) · [Français](../fr/ChromaNeural-Verified-Capabilities.md) · [日本語](../ja/ChromaNeural-Verified-Capabilities.md) · [简体中文](ChromaNeural-Verified-Capabilities.md) · [हिन्दी](../hi-IN/ChromaNeural-Verified-Capabilities.md)
## 已验证能力

ChromaNeural 0.2.21-rc.2 文档 | 未公开候选版本 | 2026年10月3日

**rc.2 文档状态：** 本候选版本尚未公开发布。本地化与可扩展 i18n 已通过本地验证；rc.2 原生构建和软件包验收仍待完成。以下安装、平台、LAN/WAN、推理及线上服务证据，除明确标为 rc.2 外，均属于历史 rc.1 证据。rc.1 下载不包含 rc.2 本地化。

## rc.2 本地化证据

Phase B/C 本地验证通过：七个交付语言的303条消息、持久选择、英语回退、输入／状态保护、模态操作及合成控制／探测检查。真实 Tk 截图与视觉验收通过。中文连接截图阻塞已定位为桌面捕获干扰，并由验证工具改为指定窗口捕获解决。已有失败记录仍保留。

可扩展 i18n 门禁也通过。单一纯数据注册表提供标识、显示名和数字格式。隔离第八目录加一个注册项通过选择、保存、回退、Windows 启动器和打包／资源发现检查，测试语言已移除。476项数字格式、2,121项消息比较通过，331个预期源哈希全部一致。这是本地源码／行为证据，不是 rc.2 原生包、线上 II 或生产验收。未公开发布 rc.2。

## 如何阅读历史 rc.1 证据

**真实物理：** 在真实机器观察通信或推理。**原生 CI：** 对应系统真实运行器构建并检查包。**本地软件：** 隔离代码／状态测试；合成后端或会话不是生产。**未验证：** 证据不足。测试环境限制不自动意味着产品失败。

### Windows

全新安装、负载完整性、内置 ICP SDK、CLI、Tk、现有状态保留和清理已验证。最终人工 GUI 观察到公开 API 响应及私人登录仍在浏览器的提示，客户端正常退出。

### Linux 与 macOS

Linux amd64 在原生 Ubuntu 24.04 构建并检查解压、完整性、SDK、CLI、Xvfb/Tk。macOS Intel 在原生 macOS 15 检查包完整性、SDK、CLI、Tk。这是真实原生运行器结果，不是所有终端系统的人工 GUI 验收。

每平台18项发布检查。Windows CI 负载与先前接受本地负载全部1,547文件一致。最终下载以 SHA-256 验证。

### 真实本地模型推理

Windows 运行内置 Qwen 后台推理。另一台 Windows 实机运行 Ollama 0.34.4 和 qwen2.5-coder:0.5b。提供者／模型与输出／队列／SQLite 哈希关联。无重复、回退、积分或发布。控制平面是隔离夹具，模型推理是真实的。

<!-- page -->
## 通信与工作流

### 两台 Windows 实机的 LAN

双向及问答返回已验证，涵盖 TLS 节点身份、字节相同、SHA-256、持久 SQLite 收件箱、重启／重试、防重复、未知节点拒绝、收到内容不执行和受控关闭。

### 经互联网和 NAT 的直接 WAN

独立移动连接上的节点直接 TCP 连到家庭网络。现有 ChromaSpeechAI 随后通过 TLS 1.3、ALPN chromaspeech-prsm-v1、批准节点认证和100,000字节负载验证。SHA-256 与字节相同；重启／重试对已收消息发送零新片段。未知节点在存储前被拒，收件箱保持持久。

反向独立发起 WAN 在现有环境无法验证，没有将覆盖网络当作替代；临时路由规则随后移除。

### 后台、资源与关联

现有队列已连接客户端后台生命周期。Windows 配置有针对租约、重试、暂停、停止、取消、重启的检查。资源约束含 CPU 调度、推理线程、提交内存，不保证总物理 RAM。

任务／节点关联使用真实本地 Windows TLS、SQLite 测试，该项 AI／后端为模拟。节点本地设置和授权连接用 Windows SDK 对接本地 PocketIC 的现有 WASM，不是线上准入。

### 隐私、审查与发布

私人端点防护、所有者隔离、缓存／会话清理、下载完整性本地验证。全局审计限既有管理员角色，不新增私人记录内容访问权。现有发布测试保留验证、同意、角色和后端接受，不证明新的生产部署。

<!-- page -->
## 修正与剩余限制

### 实际修正的缺陷

- Windows 全新发行缺 SDK：构建时打包既有锁定 @icp-sdk/core 5.4.0 及十个运行依赖，不升级、不要求终端 npm 安装。
- 缺失任务／节点消息联系：通过现有身份、队列和收件箱连接。
- 私人端点及审计元数据缺陷：本地修正，不改变 Internet Identity、所有者模型、Candid 或稳定架构。
- Windows 打包 PowerShell 模块发现及长短临时路径处理已修正，历史失败 CI 保留。

BigInt 导出修正属于兼容性，不是所有环境都复现的运行故障。相关字节和契约不变时复用旧 PASS。本次展示更新不是新一轮功能测试。

### 仍未验证或未提供

- 真实线上 Internet Identity 全流程、准入、迁移。
- macOS 人工 GUI、Linux DEB 完整安装／删除。
- 独立移动测试环境的反向 WAN 发起。
- 浏览器所有者权限的原生私人文件及全局共享前私人结果直接访问。
- 受控 Ollama/Linux/macOS/GPU 贡献；通用资源共享禁用。
- 包未签名、macOS 未公证；平台图标限制另有文档。

官方 Android 和 iOS 支持延期。

### 硬件与可复现性

这是软件。真实 LAN/WAN 和推理支持被测机器与连接的结论。模拟、本地后端和硬件模型不证明光学／GPU／专用硬件的物理性能。

原生流程使用干净检出、固定 Actions／依赖、npm 锁和哈希检查运行资源。运行器系统及可执行元数据会影响包哈希，不承诺所有环境二进制完全一致。VERIFICATION.md 和 NATIVE_BUILD_EVIDENCE.json 标识已接受构建，哈希见 docs/DOWNLOADS.md 及发行 SHA256SUMS.txt。

MCP 仍是 rc.2 之后需要单独决策和验收的功能，此处尚未实现。本文档不代表新增生产环境或 Internet Identity 变更。
