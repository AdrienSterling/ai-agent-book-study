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
| 4-1 | 主动工具发现（全量注入 vs 预筛选 vs 主动发现） | `chapter4/active-tool-discovery/` | [ch04-tools/discovery.md](ch04-tools/discovery.md) |
| 4-2 | 感知工具（仅 CLI 路径可用，MCP 服务器版本不兼容） | `chapter4/perception-tools/` | [ch04-tools/run.md](ch04-tools/run.md) |
| 4-x | 工具与 MCP（自写 Server + Client + FC 报文） | 自建 | [ch04-tools/run.md](ch04-tools/run.md) |

每个记录目录里应该有：
- `run.md` — 用了什么 provider / 模型、跑了什么命令、花了多少 token
- 原始输出（日志、报告、图）
- `observations.md` — **和书里正文说的对不对得上**，哪里不一样
- `*.patch` — 我对书里代码做的改动（书的代码不进本仓库，只留 diff）
