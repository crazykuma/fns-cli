# FNS CLI Skill

本项目包含一个可复用的 AI Agent Skill，位于 `fns-skill/` 目录中。

## 使用方法

将 `fns-skill` 目录复制到你自己的 AI Agent 的 Skills 目录中：

**Qwen Code:**
```bash
cp -r fns-skill ~/.qwen/skills/fns
# 或项目级
cp -r fns-skill .qwen/skills/fns
```

**Claude Code / 其他支持 SKILL.md 的 Agent:**
```bash
cp -r fns-skill ~/.claude/skills/fns
```

## 内容

`fns-skill/SKILL.md` 包含了 FNS CLI 的完整使用说明，包括：
- 安装和首次配置
- 笔记 CRUD 操作
- 知识发现和图谱（反向链接、出站链接）
- 分享和元数据管理
- AI Agent 工作流示例

该 Skill 设计为独立可移植的，不依赖本项目的其他部分。
