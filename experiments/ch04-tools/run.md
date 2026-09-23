# 第四章 · 工具与 MCP — 运行记录（Task 2 打卡）

| | |
|---|---|
| 日期 | 2026-09-23 |
| 模型 | Moonshot **kimi-k2.6** |
| 环境 | Python 3.13.3 |

---

## 〇、Function Calling 的原始报文

> 第四章默认你已经会 Function Calling，机制其实在第一章 §3 和第二章 §1。
> 这个脚本把一次交换的四段真实 JSON 全打出来，无框架、无循环、无抽象。

```bash
python function_calling_walkthrough.py
```

要点三条：`arguments` 是**字符串**不是对象；`tool_call_id` 必须原样回引；`finish_reason` 从 `"tool_calls"` 变成 `"stop"` 就是停止条件的真身。

**Function Calling 与 MCP 的关系**：前者是「模型 ↔ 你的代码」的接口，后者是「你的代码 ↔ 工具提供方」的接口。MCP 的 `tools/list` 拿回定义 → 填进 Function Calling 的 `tools` 参数 → 模型返回 `tool_calls` → 你转成 MCP 的 `tools/call` 执行 → 结果变回 `role:"tool"` 消息。**MCP 从不和模型直接对话。**

---

## 一、一次完整的 Tool Calling 流程（打卡要求 ②）

用**我自己写的 Agent**（`agent/`，不依赖任何框架）跑通。命令：

```bash
cd agent
python main.py --show-trajectory
```

任务：`Q1 2.5M USD, Q2 2.1M EUR, Q3 1.8M GBP, Q4 380M JPY，求年度总收入和季度平均`

**四步流程，在轨迹里一一对应：**

| 步骤 | 发生了什么 | 轨迹里的位置 |
|:--:|---|---|
| **① 声明** | 把 `convert_currency` / `calculate` 的名称、用途、参数 schema 放进上下文。**没声明的工具对模型等于不存在。** | 静态前缀（不进轨迹） |
| **② 判断** | 模型自己认定：USD 不用换，另外三种要换 → **一次并行发出 3 个 `convert_currency`** | `1 assistant` |
| **③ 获取** | Harness 校验参数 → 执行 → 结果以 `role: "tool"` **追加**到轨迹，且必须紧跟在发起它的那次调用之后 | `2/3/4 tool` |
| **④ 回答** | 模型看到结果 → 再调 2 次 `calculate` → 拿到结果后**不再调用任何工具**，直接作答。**"没有工具调用"就是停止条件。** | `5 assistant` → `6/7 tool` → `8 assistant` |

实际轨迹：

```
 0 user       Company quarterly revenue: Q1 2.5M USD, Q2 2.1M EUR, ...
 1 assistant  convert_currency({"amount":2100000,"from":"EUR","to":"USD"}) + convert_currency(...) + convert_currency(...)
 2 tool       {"result": 2282700.0, "pair": "EUR->USD"}
 3 tool       {"result": 2278800.0, "pair": "GBP->USD"}
 4 tool       {"result": 2542200.0, "pair": "JPY->USD"}
 5 assistant  calculate({"expression":"2500000 + 2282700 + 2278800 + 2542200"}) + calculate(...)
 6 tool       {"result": 9603700}
 7 tool       {"result": 2400925.0}
 8 assistant  **Annual total revenue (USD):** $9,603,700
            **Quarterly average revenue (USD):** $2,400,925
```

**3 轮、5 次工具调用**完成。同时打印了 token 账本：

```
  turn  1 | msgs 2 | in   260               | out 270 | cum_in   260 | convert_currency x3
  turn  2 | msgs 6 | in   629 cache_hit=256 | out 177 | cum_in   889 | calculate x2
  turn  3 | msgs 9 | in   852 cache_hit=512 | out  73 | cum_in 1,741 | -

  cumulative INPUT tokens    1,741   <- 随轮数 ~O(n^2)
  cumulative NEW content       520   <- 随轮数 ~O(n)
  你为"重读"付了 3.3 倍   |  缓存命中 768 (44% of input)
```

> **三个点值得注意**：
> ① 第 1 轮就**并行**发了 3 个调用——感知/纯计算类工具无副作用，天然适合并行（第四章「只读性带来的工程红利」）。
> ② `cache_hit` 从 0 → 256 → 512：静态前缀稳定，所以缓存在涨（第二章）。
> ③ 3 轮就付了 3.3 倍的重读成本——这就是第一章思考题 #2 的 O(n²)。

---

## 二、MCP：协议三步（打卡要求 ①）

```bash
cd experiments/ch04-tools
python mcp_client_demo.py
```

自己写了一台 MCP 服务器（`mcp_server.py`，把上面 agent 的两个工具用 `FastMCP` 暴露出去）
和一个最小客户端（`mcp_client_demo.py`），把协议的三步逐步打印出来：

```
1. transport   以子进程方式通过 stdio 启动服务器
               （同一台服务器也可用 Streamable HTTP 远程暴露，协议不变，只换传输层）

2. initialize  握手
   server name    : my-agent-tools
   protocol       : 2025-11-25
   capabilities   : ['prompts', 'resources', 'tools']   <- MCP 的三类原语

3. tools/list  服务器交回工具定义
   - convert_currency   required: ['amount','from_currency','to_currency']
   - calculate          required: ['expression']

4. tools/call  真实调用
   request  : {"name":"convert_currency","arguments":{"amount":2100000,"from_currency":"EUR","to_currency":"USD"}}
   response : {"result": 2282700.0, "pair": "EUR->USD"}
```

**关键理解**：客户端**从头到尾没有 import 过工具的代码**。它通过协议知道了工具存在、知道了参数 schema、并完成了调用——这就是「一次开发，处处可用」。

⚠️ 而风险也来自同一处：**这些 description 会原样进入模型上下文**。恶意服务器可以在描述里夹带指令（**工具描述投毒**，本质是提示注入的变种）。所以第四章要求：**把 description 当作不可信输入来审计、锁定服务器版本、给每台服务器最小权限凭证。**

---

## 三、为什么 Agent 需要 Tools（打卡要求 ②的前半）

第一章那条结论在这里被实测证实：**没进上下文的信息对模型等于不存在；动作接口不给的操作，模型知道也只能口头建议。**

验证方式（同一个 agent，一个开关）：

```bash
python main.py --ablate tool_definitions --show-trajectory
```

拿掉工具定义后，Agent **不会报错、不会沉默**——它照样给出一份排版工整、语气笃定的答案，数字来自参数记忆。
> **"给出了回答" ≠ "完成了任务"。**

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `../../agent/loop.py` | ReAct 循环本体（本次补完，`test_loop.py` 6/6 通过） |
| `../../agent/harness.py` | 工具定义 + 校验 + 执行（Harness） |
| `function_calling_walkthrough.py` | 一次 Function Calling 交换的原始报文（四步） |
| `mcp_server.py` | **自己写的 MCP 服务器**（FastMCP，2 个工具）← 对应【扩展】 |
| `mcp_client_demo.py` | 最小 MCP 客户端，逐步打印协议三步 |

`mcp_client_demo.py` 也可指向任意其他 MCP 服务器：`python mcp_client_demo.py <server.py>`

## 五、踩到的坑

书里 `chapter4/perception-tools` 的服务器和 `run_experiment_4_2.py` 都是针对**旧版 mcp SDK** 写的，
在当前版本下直接 `ImportError`（`MCPServer` / `Client` 均已改名）。
CLI 那条路是通的（`python cli.py list` 列出 54 个工具、`cli.py run weather location=Paris` 调用成功），
但 MCP 协议那条路走不通，所以改为自己写服务器——反而正好满足【扩展】要求。

## 六、待办

- [ ] 第四章思考题 Q1 还没答（MCP 最需要扩展什么能力）
- [ ] Q3、Q4 的批注已写进笔记，需要重答
- [ ] 把 agent 接到 MCP 服务器上（现在工具还是硬编码在 harness.py 里）
