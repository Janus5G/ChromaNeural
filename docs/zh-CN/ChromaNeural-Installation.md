# ChromaNeural

[English](../en/ChromaNeural-Installation.md) · [Dansk](../da/ChromaNeural-Installation-DA.md) · [Deutsch](../de/ChromaNeural-Installation.md) · [Français](../fr/ChromaNeural-Installation.md) · [日本語](../ja/ChromaNeural-Installation.md) · [简体中文](ChromaNeural-Installation.md) · [हिन्दी](../hi-IN/ChromaNeural-Installation.md)
## 安装

ChromaNeural 0.2.21-rc.2 文档 | 未公开候选版本 | 2026年10月3日

**rc.2 文档状态：** 本候选版本尚未公开发布。本地化与可扩展 i18n 已通过本地验证；rc.2 原生构建和软件包验收仍待完成。以下安装、平台、LAN/WAN、推理及线上服务证据，除明确标为 rc.2 外，均属于历史 rc.1 证据。rc.1 下载不包含 rc.2 本地化。

## 历史 rc.1 安装参考

目前没有公开 rc.2 软件包。以下文件名和命令故意保留 rc.1，不会安装语言选择器或注册表。已准备好的本地 rc.2 可用 --language 选择仅本次启动语言，Windows 接受 -Language；GUI 选择会保存。不要重命名 rc.1 包或替换成未经验证的 rc.2 URL。

## 安装之前

从官方发布下载：

../../RELEASE_NOTES.md

准确选择平台和架构。软件包未签名、macOS 未公证，系统可能警告或阻止。不要全局禁用安全保护；先确认来源和校验值再决定打开。

- Windows x64：ChromaNeural-0.2.21-rc.1-windows-x64.exe
- Linux amd64：chromaneural_0.2.21.rc.1_amd64.deb
- macOS Intel x86_64：ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
- 源快照：ChromaNeural-0.2.21-rc.1-source.zip
- 校验值：SHA256SUMS.txt

GitHub 将 DEB 下载名 ~rc.1 规范为 .rc.1。字节和 SHA-256 不变，内部 Debian 版本仍为 ~rc.1。

### 检查 SHA-256

在下载文件目录运行对应命令。

Windows PowerShell：
```
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.1-windows-x64.exe'
```

Linux：
```
sha256sum chromaneural_0.2.21.rc.1_amd64.deb
```

macOS：
```
shasum -a 256 ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
```

将全部64字符与 SHA256SUMS.txt 中准确文件名对应行比较，不符即停止。校验验证字节完整性，不独立证明发布者身份。五个公开哈希也见 docs/DOWNLOADS.md。

<!-- page -->
## Windows x64

### 前提

安装 Python 3.14、Tk、py/pyw 启动器及 Node.js 24。EXE 是每用户离线安装程序，不是完全冻结的 Python/Node 运行时。临时解压与安装约需 2 GB 空间。

### 步骤

1. 按上述方法验证 EXE。
2. 打开并阅读 OS 警告后确认安装。
3. 程序安装于版本目录：
```
%LOCALAPPDATA%\Programs\ChromaNeural\0.2.21-rc.1
```
4. 在该目录运行 Start-ChromaNeural.ps1，例如：
```
& "$env:LOCALAPPDATA\Programs\ChromaNeural\0.2.21-rc.1\Start-ChromaNeural.ps1"
```
5. 首次保存资源偏好，可在登录与连接页检查公开 API。

日志为 %TEMP%\ChromaNeural-install.log。拒绝已有目标，不是自动原位升级器。不自动参与、不注册开机启动，也不自动创建桌面快捷方式。

ICP SDK 及锁定依赖已含，无需为安装运行 npm ci，也不要将 NODE_PATH 指向旧开发环境。

### 删除与用户状态

完全退出。只删除版本安装目录会移除程序。%LOCALAPPDATA%\ChromaNeural\client 的状态、所选工作区和独立身份目录应保留，或由您明确决定单独处理。不含自动卸载器。

<!-- page -->
## Linux amd64

原生验证配置是 Ubuntu 24.04 amd64，不涵盖所有发行版或版本。WSL 不替代原生 Linux 软件包验证。

需要 Python 3.11+、Tk、发行版 cryptography、Node.js 20+、libgomp1；用发行版包管理器安装依赖。在下载目录：
```
sudo apt install ./chromaneural_0.2.21.rc.1_amd64.deb
```

通过菜单或命令启动：
```
chromaneural
```

程序在 /opt/chromaneural，启动器在 /usr/bin/chromaneural，桌面元数据在 /usr/share/applications/chromaneural.desktop。无安装后 npm 网络下载，无自动用户状态迁移。

原生构建、解压、完整性、SDK、CLI、Xvfb/Tk 已验证；完整 dpkg 安装／移除尚未验证。已发布 desktop 项无产品专用图标引用，但仍可启动。

## macOS Intel x86_64

需要 macOS 15+、带可用 Tk 的 Python 3.14、Node.js 24。固定加密依赖使用同一 Python。由已接受源快照根目录运行：
```
python3 -m pip install --require-hashes -r packaging/requirements-runtime.txt
```

锁定 cryptography 46.0.5、cffi 2.1.1、pycparser 3.0。这是运行前提，不是索取 II 凭据。

解压 ZIP，把 ChromaNeural.app 移到 Applications，检查来源和系统警告后打开。仅 Intel；Universal 2、Apple Silicon、Rosetta 不属于本版已接受配置。

原生构建、完整性、SDK、CLI、Tk 已验证，人工 GUI 未验证。包未签名、未公证、无专用应用图标。macOS 不含 Qwen/llama.cpp 运行时。明确选择的本地 Ollama 适配器需要另装模型，不支持受控后台贡献。

<!-- page -->
## 首次启动及后续

![实际 Windows 资源设置，窗口装饰可能因平台不同。](../images/chroma-neural-resources.png)

选择并保存偏好。概览仅显示确认数字；横线不承诺收益。通用资源共享禁用。**Afslut ChromaNeural** 完全退出。

启动失败先检查前提和正确包／架构，保留现有状态，不重置身份、不在问题报告发布私人数据。参见用户和隐私指南。

安装不改变 Internet Identity、生产后端或浏览器会话。公开 API 可达已在 Windows 验证。实际线上 II 全流程、准入和迁移仍未验证。

官方 Android 和 iOS 支持延期。

在线文档可能新于不可变 RC 二进制及源 ZIP。不会仅因文档或图标更新替换发行文件。图标状态见 docs/BRANDING.md。

MCP 仍是 rc.2 之后需要单独决策和验收的功能，此处尚未实现。本文档不代表新增生产环境或 Internet Identity 变更。
