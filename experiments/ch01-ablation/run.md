# 实验 1-1 · 上下文消融 — 运行记录

| | |
|---|---|
| 日期 | 2026-09-16 |
| 书里代码 | `bojieli/ai-agent-book` @ `33918d7` → `chapter1/context/run_experiment_1_1.py` |
| Provider / 模型 | Moonshot **kimi-k3** |
| 环境 | Python 3.13.3，`uv sync --extra ch1` |
| 五组 | `full` / `no_history` / `no_reasoning` / `no_tool_calls` / `no_tool_results` |
| 验收 | `canonical_run=True`，**Promoted to validation/latest.json** |

```bash
# 书的仓库 clone 在 D:\AI Coding\ai-agent-book（与本仓库平级）
cd chapter1/context
../../.venv/Scripts/python.exe run_experiment_1_1.py --provider kimi \
    --output-dir "D:/AI Coding/Ai Agent Book/experiments/ch01-ablation"
```

## 结果

| 组 | 结果 | 和正文说的一致？ |
|---|---|:--:|
| `full` | `correct` | ✅ |
| `no_history` | `no_terminal_response`（重复动作直到耗尽预算） | ✅ |
| `no_tool_results` | `no_terminal_response`（盲目重试） | ✅ |
| `no_tool_calls` | `no_unsupported_numbers`（**没有编造数字**） | ⚠️ 见 observations |
| `no_reasoning` | **`correct`** | ❌ **正文说会退化，实测没有** |

```json
"manuscript_behavior_claims": {
  "full_baseline_correct": true,
  "without_tool_definitions_no_tool_action": true,
  "without_tool_results_repeated_action": true,
  "without_history_repeated_action": true,
  "without_reasoning_degraded": false,
  "all_manuscript_behavior_claims_observed": false
}
```

## 开销

| | prompt | completion | cached_prompt | reasoning | total |
|---|---|---|---|---|---|
| 五组 canonical | 18,217 | 6,047 | **10,752** | 2,597 | 24,264 |
| 自加对照（unguarded） | 247 | 1,847 | 0 | 1,440 | 2,094 |

`cached_prompt_tokens 10,752 / 18,217 = 59%` —— 前缀缓存真的在命中。

## 自己加的对照组

书里的 runner 有个 `--task guarded|unguarded` 开关：`guarded`（默认）在提示词里禁止模型自估汇率，`unguarded` 把这句话拿掉。
只跑 `no_tool_calls` 这一组做 A/B，结果见 [`../ch01-ablation-unguarded/`](../ch01-ablation-unguarded/) 与 observations.md。

```bash
../../.venv/Scripts/python.exe run_experiment_1_1.py --provider kimi \
    --task unguarded --modes no_tool_calls \
    --output-dir "D:/AI Coding/Ai Agent Book/experiments/ch01-ablation-unguarded"
```

（子集运行会以 exit code 1 结束并提示 `Not promoted to validation/latest.json (canonical_run=False)`——这是设计如此，不是失败：只跑一部分组就不算 canonical run。）

## 产物

- `evidence.json` — 每一次 API 请求与响应的完整记录（已脱敏），`evidence.sha256` 是它的指纹
- `../ch01-ablation-console.log` — 完整控制台输出
