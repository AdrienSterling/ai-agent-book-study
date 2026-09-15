# agent/ — 贯穿十章的 Agent

一个 agent，每章加一层。不用框架，只用 OpenAI 兼容 SDK。

## 现在的结构（第一章）

| 文件 | 职责 | 对应书里的 |
|---|---|---|
| `loop.py` | **ReAct 循环本体** | 图1-4 的伪代码骨架 |
| `harness.py` | 组装上下文、暴露工具、约束调用、执行 | Harness = context + tools + constrain |
| `model.py` | 决策核心；真模型 + 离线假模型 | Model |
| `trace.py` | token 计量与曲线 | 思考题 #2 |
| `main.py` | CLI 接线 | — |
| `test_loop.py` | 离线自测，6 个用例 | — |

边界（这是第一章最容易记混的地方）：
- **Harness** = `harness.py` 里的 `Harness` 类 —— 工具定义、调用适配、权限校验、上下文组装
- **Environment** = `harness.py` 底部那两个 `_convert_currency` / `_calculate` 实际触碰的东西
- **Model** = `model.py`，只做一件事：context 进，decision 出

## 跑

```bash
uv run python test_loop.py            # 自测，无需 API key
uv run python main.py --simulate 16   # 离线，看累计 token 曲线
uv run python main.py                 # 真模型
uv run python main.py --list-models   # 看当前 provider 有哪些模型
```

Provider 自动探测环境变量里第一个存在的 key（`MOONSHOT_API_KEY` → `DEEPSEEK_API_KEY` → `OPENAI_API_KEY`），
也可以 `--provider` / `--model` 显式指定，或用 `.env.example` 配。

## 消融实验（书里的实验 1-1）

```bash
uv run python main.py --ablate tool_definitions --show-trajectory
uv run python main.py --ablate tool_results
uv run python main.py --ablate reasoning
uv run python main.py --ablate history
```

看的不是「有没有报错」，而是**它给出的那个答案对不对**。
拿掉工具定义之后它照样会给你一个排版工整、语气笃定的数字——那个数字来自参数记忆。

## 自己加的对照组（书上没有的）

- [ ] 第 6 组：保留工具定义，但把 `convert_currency` 的 `description` 改成空字符串或误导性描述，
      看模型还能不能选对工具、参数传得对不对。验证「接口是模型与工具之间唯一的沟通通道」。
