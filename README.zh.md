**Languages**: [🇺🇸 English](README.md) | 🇨🇳 中文

---

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
连接到你的 FNS 服务器实例。
```bash
fns login <用户名或邮箱> <密码>
```

### 2. 浏览笔记
浏览你的笔记库目录。
```bash
fns list
# 搜索特定笔记
fns list "日记"
```

### 3. 读写笔记
与特定笔记交互。
```bash
# 读取笔记
fns read "daily/2024-05-20.md"

# 创建或覆盖笔记
fns write "drafts/ideas.md" "这里有一个绝妙的点子..."

# 追加内容 (智能换行)
fns append "daily/2024-05-20.md" "- [x] 完成任务 A"
```

### 4. 上传本地文件
使用 `@` 前缀上传你机器上的本地文件。
```bash
fns write "backup/会议记录.md" @/path/to/notes.txt
# append 同样支持 @ 前缀
fns append "daily/2024-05-20.md" @/path/to/todo-list.md
```

### 5. 配置 Vault (可选)
如果你需要修改默认的 Vault 名称（需与服务器端的 Obsidian Vault 名称一致）：
```bash
fns config vault "My Vault"
```

## 🤖 AI Agent 集成

你可以配合 AI 编码助手（如 OpenCode, Claude Code, OpenClaw 等）使用 `fns` 来管理你的知识库：

- **读取上下文**：让 Agent `fns read` 特定笔记，为编码或任务提供长期记忆或背景信息。
- **自动文档**：让 Agent 将变更日志或总结通过 `fns append` 自动追加到你的日记中。
- **知识检索**：在开始任务前，使用 `fns list` 让 Agent 发现相关文件。

**配合 OpenCode/Claude Code 示例：**
```bash
# 让 OpenCode 读取总结并更新笔记
opencode "读取 'drafts/ideas.md'，总结关键点，并把总结追加到文件末尾。"
```

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
