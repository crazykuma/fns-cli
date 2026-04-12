# FNS CLI (快速笔记同步命令行工具)

这是一个强大的命令行工具，用于与 Obsidian 的 **Fast Note Sync (FNS)** 服务进行交互。让你可以直接在终端中管理、读取、写入和同步笔记。

## ✨ 功能特点

- **笔记同步**：通过 FNS 瞬间读写你的 Obsidian 笔记。
- **智能追加**：自动处理换行符，确保追加内容与原文完美融合。
- **跨平台**：兼容 macOS/Linux/Windows (Python 3.6+)。
- **本地文件上传**：支持将本地文件直接上传到笔记库。
- **零依赖**：仅使用 Python 标准库和 `curl`。

## 📦 安装

### 源码安装 (推荐)

```bash
git clone https://github.com/crazykuma/fns-cli.git
cd fns-cli
pip install -e .
```

安装完成后，你就可以在终端直接使用 `fns` 命令。

## ⚙️ 配置

**重要**：首次使用前，必须先配置你的 FNS 服务器地址。

```bash
# 设置 API 地址 (必须)
fns config url "https://your-fns-server.com/api"
```

## 🚀 快速开始

### 1. 登录
```bash
fns login <用户名或邮箱> <密码>
```

### 2. 浏览笔记
```bash
fns list
# 搜索特定笔记
fns list "日记"
```

### 3. 读写笔记
```bash
# 读取笔记
fns read "daily/2024-05-20.md"

# 创建或覆盖笔记
fns write "drafts/ideas.md" "这里有一个绝妙的点子..."

# 追加内容 (智能换行)
fns append "daily/2024-05-20.md" "- [x] 完成任务 A"
```

### 4. 上传本地文件
```bash
fns write "backup/会议记录.md" @/path/to/notes.txt
```

## 🤖 与 AI 编码助手配合使用

你可以直接在终端中通过 AI 工具（如 Claude Code, OpenCode, OpenClaw 等）来操作笔记，实现自动化记录和管理：

### OpenCode / Claude Code
你可以直接给这些 AI 编码助手发送指令，它们会自动调用本地的 `fns` 命令。

**OpenCode 示例：**
```bash
opencode "帮我读取 daily/2024-04-12.md，总结今天的待办事项，并把总结追加到该文件末尾。"
```

**Claude Code 示例：**
```bash
claude "搜索所有包含 '会议' 的笔记，把最新的会议笔记内容提取出来，并创建一个新的文件 'daily/summary.md' 进行汇总。"
```

### 通用 Agent (OpenClaw 等)
任何具有 Shell 执行能力的 AI Agent 都可以通过运行 `fns list`、`fns read` 等命令来获取笔记上下文，或者通过 `fns write`、`fns append` 自动将运行结果或总结写入你的 Obsidian 库中。

## 📁 目录结构

```
fns-cli/
├── fns.py        # 核心 CLI 逻辑
├── setup.py      # 安装脚本
├── README.md     # 英文说明
├── README.zh.md  # 中文说明
└── LICENSE       # MIT 协议
```

## 🔗 相关项目

- **[obsidian-fast-note-sync](https://github.com/haierkeys/obsidian-fast-note-sync)**: 为本工具提供支持的原始 FNS 服务和 Obsidian 插件。

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。
