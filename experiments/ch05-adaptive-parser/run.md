# 实验 5-10 · 自适应日志解析（自愈闭环）— 运行记录

| | |
|---|---|
| 书里的代码 | `chapter5/adaptive-log-parser/demo.py` |
| 模型 | **DeepSeek**（`deepseek-chat`） |
| 改动 | **零改动**——它读 `OPENAI_API_KEY` + `OPENAI_BASE_URL`，直接指向 DeepSeek 即可 |
| 自加对照 | **格式演进 vs 疑似 bug**（书里没有，对应第五章思考题 Q3） |

## 怎么跑

```powershell
& "D:\AI Coding\ai-agent-book\.venv\Scripts\Activate.ps1"
cd "D:\AI Coding\ai-agent-book\chapter5\adaptive-log-parser"

$env:OPENAI_API_KEY  = $env:DEEPSEEK_API_KEY
$env:OPENAI_BASE_URL = "https://api.deepseek.com/v1"
$env:MODEL           = "deepseek-chat"

python demo.py --offline     # 离线机制自检，不花钱
python demo.py               # 真实生成（DeepSeek）
python demo.py --log-file "...\logs_A_evolution.log"   # 自加对照
```

---

## 这个实验在演示什么：自愈闭环

```
一行日志 → [解析引擎] 依次尝试已注册的解析器
              ├── 有人认识 → 输出结构化字段 ✅
              └── 都不认识 → 不报错，触发自愈：
                     失败样本 + 报错 → Agent 生成 parse() 代码
                            ↓
                     自动测试（数据结构断言，3 个样本）
                            ↓
                     通过才热更新注册 + 持久化到 parsers/
                            ↓
                     重启后直接加载，不再调用 Agent
```

**关键设计：生成、验证、加载三者分开。** 没通过测试的代码根本进不了引擎。
这就是第一章 Harness 五要素里的**验证**和**纠正**，落成了可运行的代码。

## 结果一：两种新格式，DeepSeek 第一次就生成成功

| 格式 | 结果 |
|---|:--:|
| 新格式 A（竖线分隔） | ✅ 一次通过 |
| 新格式 B（嵌套括号） | ✅ 一次通过 |
| 持久化复用（重启后混合格式全解析） | ✅ |

---

## 结果二 ⭐ 自加对照：生成的代码 vs 预置的代码

离线模式用的是**预置（canned）解析器**，真实模式是 **DeepSeek 现场生成**。拿同一批数据喂给两者：

| 输入 | canned（预置） | DeepSeek 生成 |
|---|---|---|
| 正常行 | ✅ 解析 | ✅ 解析 |
| **格式演进**（kv 块新增 `retry` / `exit_code`） | ❌ **误报异常** | ✅ **正确适应**（8 个字段） |
| **疑似 bug**（`[NaN]` / `[2026-13-45 99:99:99]` / `[]`） | ⚠️ **静默接受** `timestamp='NaN'` | ✅ **报告异常**（返回 None） |

**两者犯的错恰好互补，而且都源自同一处设计选择：**

```python
# canned：kv 块硬编码 → 新增字段就崩；timestamp 通配 → 什么垃圾都收
r"\{latency_ms=(?P<latency_ms>\d+) status=(?P<status>\w+)\}"
r"\[(?P<timestamp>.*?)\]"

# DeepSeek：kv 块通用解析 → 新增字段照收
for pair in kv.split():
    k, v = pair.split('=', 1)
# DeepSeek：timestamp 用 strptime 校验 → 坏数据拒绝
try:
    datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
except ValueError:
    return None
```

### 这正好回答了第五章思考题 Q3

> 题目：Agent 应该如何区分「需要适应的变化」和「需要报告的异常」？

**答案不是让 Agent 去判断，而是让生成的解析代码在不同字段上采取不同的松紧度：**

> ## **结构宽松，值严格。**
> **允许新增字段（结构演进是常态），但校验每个字段的类型和值域（值出错就是 bug）。**

`canned` 把两者做反了——结构写死、值通配——于是**该适应的不适应，该报的不报**。
这不是"Agent 聪明不聪明"的问题，**是一行 `strptime` 的问题。**

### 顺带一个成本结论

A 组（新增字段）DeepSeek 版**零次 Agent 调用**就解析成功；canned 版会触发一次重新生成。
> **生成代码的泛化程度，直接决定后续要触发多少次昂贵的自愈。**

---

## 产物

| 文件 | 说明 |
|---|---|
| `logs_A_evolution.log` | 自加对照 A：格式演进（新增字段） |
| `logs_B_corruption.log` | 自加对照 B：疑似 bug（时间戳损坏） |
| `parser_comparison.md` | 两个解析器的逐行对照结果 |

## 待办

- [ ] 让自愈闭环**在 B 组上真的跑一次**：目前 `--log-file` 走的是步骤 3（明确不调 Agent）。改成触发自愈，看 Agent 面对坏数据**会不会生成一个"兼容 NaN"的解析器**——那才是题目担心的失败模式
- [ ] 加一条告警：适应新格式时把 **diff 作为可审计产物**留下，而不是静默适应
- [ ] 把这套"失败 → 生成 → 测试 → 热更新"接进我自己的 `agent/`
