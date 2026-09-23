# experiments/

书里配套实验的**运行记录**——输出、报告、我的观察。

书的代码不放这里（那是别人的仓库，clone 在 `D:\AI Coding\ai-agent-book`，与本仓库平级）。
这里只存**我跑出来的结果**和**我自己加的对照组**。

| 编号 | 实验 | 书里的目录 | 记录 |
|:--:|---|---|---|
| 1-1 | 上下文消融 | `chapter1/context/` | [ch01-ablation/](ch01-ablation/) |
| 1-2 | Kimi 原生 Agent | `chapter1/web-search-agent/` | |
| 1-3 | Deep Research 闭环 | `chapter1/search-codegen/` | |
| 1-4 | 文生图工作流 vs 原生 | `chapter1/image-gen-workflow/` | |
| 2-3 | KV Cache 与错误的上下文管理模式 | `chapter2/kv-cache/` | [ch02-kv-cache/](ch02-kv-cache/) |
| 4-x | 工具与 MCP（自写 Server + Client） | `chapter4/perception-tools/` | [ch04-tools/](ch04-tools/) |

每个记录目录里应该有：
- `run.md` — 用了什么 provider / 模型、跑了什么命令、花了多少 token
- 原始输出（日志、报告、图）
- `observations.md` — **和书里正文说的对不对得上**，哪里不一样
