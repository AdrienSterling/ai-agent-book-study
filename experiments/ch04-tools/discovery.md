# 实验 4-1 · 主动工具发现 — 运行记录

| | |
|---|---|
| 书里的代码 | `chapter4/active-tool-discovery/demo.py`（在平级的 `ai-agent-book` clone 里） |
| 对照的三种策略 | **全量注入** / **检索预筛选** / **主动发现** |
| 工具库 | 126 个工具，8 个内置任务 |
| 我的改动 | [`deepseek-provider.patch`](deepseek-provider.patch) — 加一条 DeepSeek 分支 |

## 怎么跑

```powershell
# 一次性激活 venv，之后不用写长路径
& "D:\AI Coding\ai-agent-book\.venv\Scripts\Activate.ps1"
cd "D:\AI Coding\ai-agent-book\chapter4\active-tool-discovery"

python demo.py --offline                    # 离线自检，无需任何 key
python demo.py                              # 真模型（打了补丁后走 DeepSeek）
python demo.py --tool-set-size 40           # 缩小工具库，看规模的影响
python demo.py --tasks finance+news --strategies full,discovery   # 小规模试水
```

### 打补丁

书里原版只支持 OpenAI（chat+embeddings）和 OpenRouter（chat + 本地嵌入）两条路径。
DeepSeek 和 OpenRouter 情况相同——**只有 chat completions，没有 embeddings 接口**——所以照着
OpenRouter 那个分支加了一条：对话走 DeepSeek，工具检索退用本地哈希嵌入。

```powershell
cd "D:\AI Coding\ai-agent-book"
git apply "D:\AI Coding\Ai Agent Book\experiments\ch04-tools\deepseek-provider.patch"
# 还原： git checkout chapter4/active-tool-discovery/demo.py
```

---

## 结果一：离线自检（126 工具 × 8 任务 × 3 策略）

> 离线模式用本地哈希嵌入 + 脚本化 mock 模型，**token 与延迟是真实测量**，准确率只反映启发式路由。

| 策略 | 精确选对 | 任务完成 | 平均注入 token | 总注入 token |
|---|:--:|:--:|---:|---:|
| **全量注入** | 8/8 | 8/8 | **11,630** | 93,040 |
| **检索预筛选** | **4/8** | 4/8 | 1,030 | 8,236 |
| **主动发现** | 8/8 | 8/8 | **974** | 7,796 |

> **注入 token：全量 93,040 vs 主动发现 7,796，精简约 11.9 倍。**

### 🔍 意外发现：检索预筛选只有 4/8，比全量注入还差

书里把检索预筛选讲成全量注入的改进，但实测它**掉了一半任务**。日志说明了原因——它一次性筛 10 个候选，而且筛错了：

```
任务: 帮我了解一下最近'量子计算'方面有什么新的科研进展
[检索预筛选] 预筛选命中: get_nft_metadata, get_distance, get_news_by_source,
             get_timezone, get_current_time, get_market_index, ...
             调用轨迹: []
             判定: ❌ 出错（漏用 arxiv_search）
```

查论文的任务，它返回了 NFT、时区、股票指数——**`arxiv_search` 根本没进候选池，模型再聪明也用不了。**

而主动发现同一个任务：

```
[discover_tools] need='在学术论文库检索最新论文'
                 -> ['semantic_scholar_search', 'arxiv_search', 'search_pubmed', 'search_news']
判定: ✅ 精确选对
```

**差别不在检索算法，在检索的时机和输入。**
预筛选用**用户的原始问题**做**一次性**匹配；主动发现用**模型自己想清楚后的能力描述**（"在学术论文库检索最新论文"）做匹配——后者是模型已经理解了任务之后生成的，语义精确得多。

这正好坐实了书里那句：
> 检索式预筛选的内在局限——它按用户的初始查询做**一次性**匹配，而任务开始时无法预见所有需求。

---

## 结果二：DeepSeek 真模型 · 完整版（126 工具 × 8 任务 × 3 策略）

| 策略 | 精确选对 | **任务完成** | 平均注入 token | 平均延迟 |
|---|:--:|:--:|---:|---:|
| 全量注入 | 4/8 | **8/8** | 11,630 | 8.05s |
| 检索预筛选 | 4/8 | 5/8 | 1,030 | 4.80s |
| 主动发现 | **5/8** | 5/8 | **956** | 6.16s |

> 注入 token：全量 93,040 vs 主动发现 7,651，**精简 12.2 倍**。

### ✅ 复现了的：token 与延迟

**12.2 倍的 token 精简**，铁一样硬。延迟上主动发现（6.16s）也快过全量注入（8.05s）。
这两条和书里仓库的验收记录一致：「主动发现的 schema 暴露和实测用时显著更低」。

### ❌ 没复现的：准确率提升 —— 而且**书自己就是矛盾的**

| 出处 | 说法 |
|---|---|
| 正文实验 4-1 | 「预期观察：**准确率和任务完成率显著提升**」 |
| 仓库 `chapter4/README.md` 验收记录 | 「两组均 3/3 完成、准确率均 100%（**未证明准确率提升**）；……但**轨迹仍含无关调用与过早结束**」 |

我的数据站验收记录这边：**精确选对 5/8 vs 4/8，n=8 时这点差距在噪声范围内。**

### 🔍 更值得记的：一个反向的发现

**全量注入的「任务完成」是 8/8，最高；主动发现只有 5/8。**

两个指标要分开读：
- **精确选对** = 覆盖全部能力槽位 **且** 没错用通用兜底工具
- **任务完成** = 把事办成了（**允许用兜底工具**）

所以真实情况是：
> **全量注入把 8 个任务全办成了，但一半用错了工具（靠 `web_search` 兜底）。
> 主动发现办成的都很精确，但有 3 个根本没办成。**

**原因**：主动发现只暴露 7 个工具，`discover_tools` 没匹配到就**没有退路**；全量注入永远有 `web_search` 当拐杖。
这正是验收记录里那句「**过早结束**」，也正是正文里预告过的降级问题：

> 若两层匹配的候选相似度都低于阈值，则应明确返回「未找到」，让 Agent 改写需求重试、用基础工具手工实现，或干脆创造一个新工具。

**降级路径没做好，省下的 token 就会变成没完成的任务。**

### ⚠️ 但这次对照有一个我自己引入的变量

**DeepSeek 没有 embeddings 接口，所以我的补丁让工具检索退用了「本地哈希嵌入」。**

- 全量注入 **不用索引** → 不受影响
- 检索预筛选、主动发现 **都靠索引** → 双双被削弱

**所以准确率那一列是不公平的**，token 和延迟那两列才是干净的。

这是实验设计里的经典错误：**我换 provider 时顺手改掉了第二个变量，却只想改一个。**
（对照第一章 `evidence.json` 里那个 `claim_qualifications` 字段——作者会主动标注哪些结论是"构造上必然成立"的。我这里应该同样标注。）

---

## 待办

- [x] ~~完整版 DeepSeek 跑~~ → 预筛选没翻盘（4/8），但发现了更重要的「完成率反向」现象
- [ ] **消除我引入的变量**：用真实嵌入模型重跑。Ollama 已装，`ollama pull nomic-embed-text` 即可，免费本地跑：
      `$env:EMBED_MODEL="nomic-embed-text"` + 把 embedder 指向 `http://localhost:11434/v1`
- [ ] 查一下那 3 个「主动发现没完成」的任务，看 `discover_tools` 到底返回了什么——**是匹配失败，还是匹配对了但模型没用**
- [ ] **我自己的对照组**：`--tool-set-size` 取 20 / 40 / 80 / 126，画出「全量注入的准确率随工具数下降」的曲线——书里没做这个
- [ ] 本地 Qwen3-4B 对照（验证书里说的"更让小参数量模型在上百工具场景下保持可用"）；受 4GB 显存限制，全量注入那组需要 `--tool-set-size` 缩小
