# AI Agent Book — 学习记录

跟读 [bojieli/ai-agent-book](https://github.com/bojieli/ai-agent-book) 的公开学习仓库：**笔记 + 一个贯穿十章的 Agent 项目**。

- 中文读原文，英文记笔记（方法见 [notes/Learning Method.md](notes/Learning%20Method.md)）
- 每章不只做书上的实验，**至少加一组自己设计的对照**
- 代码不用框架，一个 agent 从裸 ReAct loop 开始，每章往上加一层能力

---

## 进度

| 章 | 主题 | 笔记 | 贯穿项目加了什么 | 状态 |
|:--:|---|:--:|---|:--:|
| 1 | Agent 基础 | [✓](notes/Ai%20Agent%20Book.md) | 裸 ReAct loop + 消融实验开关 + token 计量 | ✅ 笔记✓ [实验1-1✓](experiments/ch01-ablation/) loop.py✓ |
| 2 | 上下文工程 | [✓](notes/Ai%20Agent%20Book.md) | 上下文压缩 / 前缀稳定性 | 笔记✓ [实验2-3✓](experiments/ch02-kv-cache/) |
| 3 | 用户记忆与知识库 | [✓](notes/Ai%20Agent%20Book.md) | 用户记忆 + RAG | 笔记✓ |
| 4 | 工具 | [✓](notes/Ai%20Agent%20Book.md) | 自写 MCP Server + 客户端 | 笔记✓ [实验4-1✓](experiments/ch04-tools/discovery.md) [自建✓](experiments/ch04-tools/run.md) |
| 5 | Coding Agent 与通用 Agent | | 验证与纠正（Harness） | |
| 6 | 交互 | | 扩展观察 / 动作空间 | |
| 7 | Agent 评估 | | 写 eval | |
| 8 | 模型后训练 | | 跑通一次后训练 | |
| 9 | 持续进化 | | 从轨迹生成更新 | |
| 10 | 多 Agent 协作 | | 拆成多 Agent | |

每章结束打一个 tag（`git tag ch01`），`git diff ch01..ch02` 就是那一章真正加的东西。

---

## 贯穿项目

代码在 [`agent/`](agent/)。第一章的产物是一个**不依赖任何框架**的 ReAct 循环，刻意做了三件事：

1. **每轮重建 context = 静态前缀 + 轨迹**，让这个公式变成能跑的代码而不是一句话。
2. **`--ablate` 开关**复现书里的实验 1-1：拿掉工具定义 / 工具结果 / 思考过程 / 历史消息，看 Agent 怎么失败——它几乎从不报错，只是给出一个看上去毫无破绽的答案。
3. **token 计量**：把「累计输入 token 随轮数二次方增长」这件事画出来，而不是背下来。这是第一章思考题 #2，也是第二章的全部动机。

```bash
cd agent
uv run python test_loop.py           # 离线自测，不花钱
uv run python main.py --simulate 16  # 离线看 O(n^2) 曲线
uv run python main.py                # 真模型跑默认任务
uv run python main.py --ablate tool_definitions --show-trajectory
```

---

## 实验记录

书里配套实验的运行结果在 [`experiments/`](experiments/)，书的代码本身不放这里。

**实验 4-1（主动工具发现，DeepSeek + 离线对照）**：126 个工具下，全量注入每任务 **11,630 token**，主动发现只要 **974**——精简 **11.9 倍**。token 与延迟**完全复现**；但**准确率提升没有复现**——而书里正文的「预期观察」与仓库自带的验收记录本身就是矛盾的，我的数据站验收记录那边。更值得记的反向发现：**全量注入任务完成 8/8，主动发现只有 5/8**——省下的 token 变成了没完成的任务。详见 [discovery.md](experiments/ch04-tools/discovery.md)。

**第四章自建实验**：书里的 MCP 服务器与当前 SDK 不兼容，于是自己写了 MCP Server + 两个客户端（一个用官方 SDK，一个纯 JSON-RPC），外加一份 Function Calling 的原始报文走查。详见 [run.md](experiments/ch04-tools/run.md)。

**实验 2-3（KV Cache，kimi-k2.6）**：只往 system 注入动态内容，缓存占比 70.6% → **0.6%**，输入账单 **3.3 倍**，而任务照常完成、输出毫无异常——书里说的「无形成本」。滑动窗口那组则直接**任务失败**，82 次工具调用里 32 次重复。详见 [observations.md](experiments/ch02-kv-cache/observations.md)。

**实验 1-1（上下文消融，kimi-k3，五组 canonical run）已完成** —— 其中 `no_reasoning` 组
跑出了和正文不一致的结果，详见 [observations.md](experiments/ch01-ablation/observations.md)。

## 笔记

- [第一章笔记](notes/Ai%20Agent%20Book.md) — 含十道思考题的作答与批注
- [学习方法](notes/Learning%20Method.md) — 读中文 → 合上书 → 用英文凭记忆写 → 回去对照；附每章复盘日志

笔记在 Obsidian 里写，用 `scripts/sync-notes.ps1` 同步进这个仓库。
