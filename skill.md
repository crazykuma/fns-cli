# FNS CLI 使用示例

本文档提供了 FNS CLI 的常见使用场景和示例命令。

## 🔐 首次配置

### 交互式引导（推荐新手）
```bash
fns login
# 输入 FNS 服务器地址: https://your-server
# 用户名或邮箱: you@example.com
# 密码: **** (隐藏输入)
# 📦 可用 Vault:
#   1. defaultVault
# 选择 Vault [1]: 1
# 🎉 配置完成! 试试: fns list
```

### 命令行快速配置
```bash
fns login -u https://your-server username password
fns config vault defaultVault
```

### 查看当前配置
```bash
fns config show
# 📋 Current configuration:
#   API URL : https://your-server/api
#   Vault   : defaultVault
#   User    : yourname
```

## 📝 笔记基础操作

### 读取笔记
```bash
# 读取指定笔记
fns read "daily/2024-05-20.md"

# 以 JSON 格式输出（适合 AI 解析）
fns read "daily/2024-05-20.md" --json

# 静默模式（只输出内容，无额外提示）
fns read "daily/2024-05-20.md" -q
```

### 创建和更新笔记
```bash
# 直接写入内容
fns write "drafts/ideas.md" "这是我的新想法..."

# 从本地文件上传
fns write "backup/会议记录.md" @/path/to/meeting-notes.txt
```

### 追加内容（智能换行）
```bash
# 追加文本（自动处理换行）
fns append "daily/2024-05-20.md" "- [x] 完成任务 A"

# 从文件追加
fns append "daily/2024-05-20.md" @/path/todo-list.md
```

### 在开头插入内容
```bash
# 在 Frontmatter 后插入内容
fns prepend "daily/2024-05-20.md" "---\ntags: [已审核]\n---\n\n"
```

## 🔍 查找和管理笔记

### 列出和搜索笔记
```bash
# 列出所有笔记
fns list

# 搜索关键词
fns list "日记"
fns list "project"

# 指定页码
fns list --page 2
```

### 查看目录树
```bash
# 查看整个 Vault 结构
fns tree

# 查看子目录
fns tree "projects"
```

### 移动/重命名笔记
```bash
fns move "drafts/ideas.md" "archive/ideas-2024.md"
```

### 查找和替换
```bash
# 简单替换
fns replace "daily/2024-05-20.md" "TODO" "DONE"

# 正则替换（替换所有匹配项）
fns replace "notes.md" "\[ \]" "[x]"
```

### 删除和恢复
```bash
# 删除笔记（移入回收站）
fns delete "old-notes.md"

# 查看回收站
fns recycle-bin

# 恢复笔记
fns restore "old-notes.md"
```

### 查看历史版本
```bash
fns history "daily/2024-05-20.md"
```

## 🔗 知识图谱

### 查看反向链接
```bash
# 哪些笔记链接到当前笔记
fns backlinks "projects/architecture.md"
```

### 查看出站链接
```bash
# 当前笔记链接到哪些笔记
fns outlinks "projects/architecture.md"
```

## 🏷️ 元数据管理

### 查看 Frontmatter
```bash
fns frontmatter "daily/2024-05-20.md"
```

### 编辑 Frontmatter
```bash
# 设置标签
fns frontmatter "daily/2024-05-20.md" --set tags=重要 --set status=草稿

# 删除字段
fns frontmatter "daily/2024-05-20.md" --remove outdated-field
```

## 🔗 分享笔记

### 创建分享链接
```bash
# 基本分享
fns share "public/meeting-notes.md"

# 带过期时间
fns share "public/meeting-notes.md" --expire 24h

# 带密码保护
fns share "public/meeting-notes.md" --password secret123 --expire 7d
```

### 取消分享
```bash
fns unshare "public/meeting-notes.md"
```

## 🗄️ Vault 管理

### 查看 Vault 列表
```bash
fns vaults
```

### 查看 Vault 详情
```bash
# 查看当前 Vault
fns vault-info

# 查看指定 Vault
fns vault-info 1
```

### 创建新 Vault
```bash
fns vault-create "NewVault"
# ⚠️ Create new vault 'NewVault'? This action cannot be undone [y/N]: y
```

### 删除 Vault（双重确认）
```bash
fns vault-delete 2
# ⚠️ WARNING: This will permanently delete vault ID '2' and ALL its data! [y/N]: y
# 🚨 Are you absolutely sure? This action CANNOT be undone! [y/N]: y
```

## 🖥️ 服务器信息

### 查看版本
```bash
fns version
# 📋 Server version:
#   version: 2.0.10
#   gitTag: v2.0.10
#   buildTime: 2024-05-20T10:00:00Z
```

### 健康检查
```bash
fns health
# ✅ Server is healthy.
```

### 查看当前用户
```bash
fns info
# 👤 Current user:
#   username: yourname
#   email: you@example.com
```

## 🤖 AI Agent 集成示例

### 读取上下文 + 工作 + 记录
```bash
# 1. AI 读取项目背景
fns read "projects/architecture.md" --json

# 2. AI 工作...

# 3. AI 记录变更到日记
fns append "daily/$(date +%Y-%m-%d).md" "- 完成架构评审，更新设计文档"
```

### 自动文档更新
```bash
# 追加变更日志
fns append "changelog.md" "## v0.4.0 - $(date +%Y-%m-%d)\n- 新增 13 个命令"

# 更新项目状态
fns frontmatter "projects/active.md" --set status=完成 --set completed=$(date +%Y-%m-%d)
```

### 知识检索
```bash
# 查找相关笔记
fns list "api design"
fns backlinks "api/design-decisions.md"
```

## 🎛️ 高级技巧

### JSON 输出用于脚本
```bash
# 获取笔记列表的 JSON
fns list --json | python -c "import sys,json; print(json.load(sys.stdin)['data']['pager']['totalRows'])"

# 检查配置状态
fns config show --json 2>/dev/null || echo "配置不完整"
```

### 静默模式用于 CI/CD
```bash
# 在 CI 中上传文件
fns write "releases/changelog.md" @./CHANGELOG.md -q

# 自动追加日志
fns append "daily/$(date +%Y-%m-%d).md" "Deployed v0.4.0" -q
```

### 批量操作
```bash
# 批量替换（遍历文件列表）
for file in $(fns list "daily" --json | jq -r '.data.list[].path'); do
  fns replace "$file" "旧术语" "新术语"
done
```

## ❓ 常见问题

### 如何查看当前配置？
```bash
fns config show
```

### 如何切换用户？
```bash
fns login
# 输入新用户的凭据即可
```

### 如何切换 Vault？
```bash
fns config vault "OtherVault"
```

### 忘记服务器地址？
```bash
fns config show
# 或重新设置
fns config url https://your-server
```
