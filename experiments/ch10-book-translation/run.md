# 实验 10-2 · 书籍翻译：管理者模式 vs 单 Agent — 运行记录

| | |
|---|---|
| 日期 | 2026-10-03 |
| 书里的代码 | `chapter10/book-translation/demo.py` |
| 模型 | **DeepSeek**（`deepseek-chat`） |
| 改动 | **零改动**——它读 `OPENAI_API_KEY` + `OPENAI_BASE_URL` + `OPENAI_MODEL` |
| 规模 | 4 章英文样本书（约 5 KB），英译中 |

## 怎么跑

```powershell
& "D:\AI Coding\ai-agent-book\.venv\Scripts\Activate.ps1"
cd "D:\AI Coding\ai-agent-book\chapter10\book-translation"

python demo.py --dry-run      # 离线预演：协作图 + Manager 计划 + token 预算，不花钱

$env:OPENAI_API_KEY  = $env:DEEPSEEK_API_KEY
$env:OPENAI_BASE_URL = "https://api.deepseek.com/v1"
$env:OPENAI_MODEL    = "deepseek-chat"
python demo.py --out-dir "D:\AI Coding\Ai Agent Book\experiments\ch10-book-translation\output"
```

## 四个 Agent 在干什么

| Agent | 职责 | 上下文 |
|---|---|---|
| **Glossary** | 读全书，抽取术语，写入共享术语表 | 读全书 ≈ 1136 tok |
| **Translation** | 逐章翻译，**每章独立**，读共享术语表 | 每章 ≈ 250–300 tok |
| **Proofreading** | 读全部译文，出审校意见 | ≈ 1091 tok |
| **Manager** | 任务/计划/调用记录/文件索引，**不含正文** | ≈ 515 tok |

**它们不共享上下文，只共享一个文件：`glossary.json`。**
→ 这就是第十章「不共享上下文时如何同步信息」的实物——**共享文件系统 = Agent 世界的共享内存。**

---

## 结果

| 指标 | 管理者模式 | 单 Agent |
|---|---:|---:|
| **主/Manager 上下文峰值** | **902** | **2057** |
| Manager LLM 决策调用上下文 | 820 | — |
| **全流程总 token 消耗** | **7653** | **5966** |
| 术语内部一致率 | **100%** | 89% |
| **指定术语遵从率** | **100%** | **53%** |
| 参与 Agent 种类数 | 4 | 1 |

### 术语遵从率逐条看

| 术语 | 规定译法 | 默认译法 | 管理者 | 单 Agent |
|---|---|---|:--:|:--:|
| token | 词元 | 标记 | 4/4 | 4/4 |
| prompt | 提示词 | 提示 | 4/4 | 4/4 |
| **latency** | **时延** | 延迟 | **4/4** | **0/4** |
| **embedding** | **嵌入向量** | 嵌入 | **3/3** | **0/3** |

> `latency→时延` 和 `embedding→嵌入向量` 单 Agent **一次都没遵守**——因为它看不到共享术语表。
> **同一个模型、同一段原文，差别只在于有没有读到那张表。**

### ⚠️ 最反直觉的一格：总 token 反而更高

**7653 vs 5966 —— 管理者模式贵了 28%。**

> **多 Agent 不省总量，它压的是峰值。**
> Manager 只保存任务/计划/调用记录/文件索引，**完整译文全部落盘到文件系统**，所以**无论书有多长，Manager 上下文都基本恒定**——而单 Agent 把全部原文与译文都留在一条对话里，**上下文随书长线性膨胀**。

这正好对应第十章那条成本警告：
> 多 Agent 的收益**必须足够大，能覆盖数倍乃至一个数量级的额外开销**，否则一个调校得当的单 Agent 往往更划算。

**本次 4 章只有 5KB，所以峰值差距只有 2.3 倍。书越长，这个倍数越大，而 token 开销的 28% 是固定的**——交叉点大概在书变长之后。

---

## 产物

```
output\
├── orchestration\          ← 管理者模式
│   ├── chapter1_zh.md ~ chapter4_zh.md
│   ├── glossary.json              ← ★ 共享术语表，四个 Agent 都读它
│   └── proofreading_report.json   ← ★ 审校 Agent 的意见
└── single_agent\           ← 单 Agent 对照
    ├── chapter1_zh.md ~ chapter4_zh.md
    └── progress.json
```

一眼看出差别：

```powershell
Select-String -Path ".\output\*\chapter3_zh.md" -Pattern "时延|延迟"
```

## 待办（自己的对照组）

- [ ] **`--no-glossary`**：把共享术语表拿掉，管理者模式的遵从率会不会掉到和单 Agent 一样的 53%？
      **如果会，说明优势全部来自那张共享文件，而不是来自"多 Agent"本身。** 这是最值得做的一组。
- [ ] **`--no-proofreading`**：关掉审校 Agent 和 Manager 修订闭环，质量掉多少？
- [ ] 换更长的书，找出"峰值优势"开始压过"总 token 劣势"的交叉点
