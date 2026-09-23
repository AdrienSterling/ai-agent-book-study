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

## 结果二：DeepSeek 真模型（40 工具试水）

```
任务 [finance+news]: 苹果公司最近股价怎么样？帮我看看有没有相关新闻能解释一下原因。

[全量注入] 注入 3,791 tokens（40 个工具）延迟 7.06s
   调用轨迹: get_stock_price, search_news, get_news_by_source, search_news, web_search
   判定: ⚠️ 完成但错选（2/2 槽位命中，但错用了通用工具 web_search）

[主动发现] 注入 1,085 tokens（11 个工具）延迟 5.86s
   调用轨迹: discover_tools, get_stock_price, discover_tools, search_news, search_news
   判定: ✅ 精确选对
```

**只有 40 个工具，全量注入就已经开始乱找了**——`search_news` 调了两次，还兜底用了 `web_search`。
主动发现那组更干净，因为它**每次只面对 4 个候选**。

书里说「工具数量超过一百个时，即使最先进的模型也容易在工具选择上出错」——40 个就看见苗头了。

---

## 待办

- [ ] 完整版 DeepSeek 跑（126 工具 × 8 任务 × 3 策略），看**检索预筛选在真模型下会不会翻盘**
- [ ] **我自己的对照组**：`--tool-set-size` 取 20 / 40 / 80 / 126，画出「全量注入的准确率随工具数下降」的曲线——书里没做这个
- [ ] 本地 Qwen3-4B 对照（验证书里说的"更让小参数量模型在上百工具场景下保持可用"）；受 4GB 显存限制，全量注入那组需要 `--tool-set-size` 缩小
