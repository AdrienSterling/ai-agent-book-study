# 实验 2-3 · KV Cache 与错误的上下文管理模式 — 运行记录

| | |
|---|---|
| 日期 | 2026-09-20 → 09-21 |
| 书里代码 | `bojieli/ai-agent-book` @ `33918d7` → `chapter2/kv-cache/main.py` |
| Provider / 模型 | Moonshot **kimi-k2.6** |
| 环境 | Python 3.13.3，`uv sync --extra ch1 --extra ch2` |
| 任务 | 默认任务（在 `D:\AI Coding\ai-agent-book` 上做文件检索与阅读） |
| 跑了哪几组 | `correct` · `dynamic_system` · `sliding_window` |

```bash
cd chapter2/kv-cache
../../.venv/Scripts/python.exe main.py --no-interactive --mode correct \
    --output "D:/AI Coding/Ai Agent Book/experiments/ch02-kv-cache/result_correct.json"
# 同样方式跑 --mode dynamic_system / --mode sliding_window
```

---

## 主结果

| 策略 | 任务完成 | 轮数 | 工具调用 | **重复调用**<br>(同工具同参数) | **缓存占比** | 总耗时 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| `correct`（前缀稳定，动态信息追加末尾） | ✅ | 9 | 30 | **0** | **70.6%** | 228.4s |
| `dynamic_system`（往 system 注入动态内容） | ✅ | 9 | 30 | **0** | **0.6%** | 292.8s |
| `sliding_window`（只保留最近若干条消息） | ❌ **失败** | **30**（触顶） | **82** | **32** | 12.3% | 298.8s |

按缓存价 = 普通价 1/10 折算的**计费输入 token**：

| | 输入 token | 其中缓存命中 | 折算计费 |
|---|---:|---:|---:|
| `correct` | 279,394 | 197,120 | **101,986** |
| `dynamic_system` | 335,486 | 2,048 | **333,643** |

> **只往系统提示词里加了动态内容，输入账单变成 3.3 倍。**

## 逐轮 TTFT（首 token 延迟）

| 轮 | correct | dynamic_system | 倍数 |
|:--:|---:|---:|:--:|
| 1 | 6.19s | 6.89s | 1.1x |
| 2 | 6.18s | 7.43s | 1.2x |
| 3 | 9.77s | 8.34s | 0.9x |
| 4 | 10.23s | 10.35s | 1.0x |
| 5 | 12.93s | 14.40s | 1.1x |
| 6 | 15.55s | 22.41s | 1.4x |
| 7 | 14.38s | 30.63s | **2.1x** |
| 8 | 27.13s | 37.74s | 1.4x |
| 9 | 125.78s | 154.13s | 1.2x |

## 附：一次被中断的长跑，留下了 O(n²) 的实测数据

第一次 `--compare` 跑到一半机器休眠了（第 14 轮隔了 8 小时才报 Connection error），
但 `correct` 模式前 13 轮的逐轮数据完整有效，正好是**第一章思考题 #2** 的实测答案：

| 轮 | TTFT | 本轮输入 | 缓存命中 | 命中率 | **累计输入** |
|:--:|---:|---:|---:|:--:|---:|
| 2 | 2.65s | 681 | 256 | 38% | 681 |
| 3 | 5.43s | 5,450 | 512 | 9% | 6,131 |
| 5 | 7.32s | 6,758 | 4,096 | 61% | 18,646 |
| 7 | 14.69s | 44,588 | 18,944 | 42% | 82,251 |
| 9 | 9.08s | 66,072 | 57,344 | 87% | 205,823 |
| 11 | 9.56s | 69,318 | 67,584 | **97%** | 344,169 |
| 13 | 8.52s | 78,513 | 71,680 | 91% | **494,413** |

> **最后一轮的单次上下文只有 78,513 token，13 轮累计却付了 494,413 token —— 6.3 倍。**
> 上下文涨了 115 倍（681 → 78,513），TTFT 只涨了 3.2 倍（2.65s → 8.52s）——因为命中率爬到了 91%。

原始日志：[`console-interrupted-run.log`](console-interrupted-run.log)

## 产物

- `result_correct.json` · `result_dynamic_system.json` · `result_sliding_window.json`
- `console-interrupted-run.log` — 被休眠打断的长跑，含 13 轮逐轮数据
- 观察见 [`observations.md`](observations.md)
