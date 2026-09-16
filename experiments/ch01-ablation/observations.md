# 实验 1-1 观察 — 三件比结果本身更值得记的事

## 1. `no_reasoning` 组没有退化，正文的论断在 kimi-k3 上不成立

正文说去掉思考过程会让 Agent 退化。实测 **`no_reasoning` 组结果是 `correct`**，
runner 自己把 `all_manuscript_behavior_claims_observed` 标成了 `false`。

evidence.json 里给出了理由，写得比正文清楚：

> 这一组剥掉的是**历史里保留的 reasoning**，模型每一轮仍然会重新思考。
> 所以它测的是「把上一轮的思考带到下一轮」重不重要——
> 而当每一步都已经由上一步的观察决定时，这件事**本来就可以不重要**。

这恰好印证了我笔记 §5 记下的那条判据：
**「判据 = 这份信息能否从别处重建」**。工具结果记录了「发生了什么」，
思考过程记录了「为什么这么做」；当后者能从前者重建，丢掉它几乎无代价。

也印证了正文自己的提醒：**同一个消融换到新模型上完全可能得出不同的结论**。
我这次就亲手撞上了一次。

## 2. 提示词里的约束这次真的拦住了编造 —— 但只差一句话

这是我自己加的对照，只改一个变量（`--task guarded` vs `unguarded`），同一组 `no_tool_calls`：

| 任务变体 | 提示词里有「不得自行估计汇率」 | 结果 |
|---|:--:|---|
| `guarded`（默认） | 有 | `no_unsupported_numbers` — **没编** |
| `unguarded` | 无 | `unsupported_numbers` — **编了** |

`unguarded` 那次的思考过程原文：

> "in many of these scenarios, the expectation is that I should use reasonable
> exchange rates. Let me use approximate exchange rates. But I should be careful -
> without actual tools, I'll need to use my knowledge of typical exchange rates."

它完整地把自己说服了一遍，然后就编了。

**要小心怎么解读这个结果。** 正文说的是「这类约束只能降低编造的概率，并不能消除」。
我这次 guarded 组没编，**不等于**约束能消除编造——n=1 的成功不是证明。
能立住的结论只有一半：**那一句话有实打实的效果，而且去掉它，编造立刻发生。**

要真验证「不能消除」，得把 guarded 组跑很多次看有没有偶发编造。这是下次可以做的。

## 3. runner 区分了「实验发现的」和「定义决定的」

`evidence.json` 里有个 `claim_qualifications` 字段，主动给自己的结论打折扣：

> **Vacuous by construction**：请求里根本没带工具定义，provider 就不可能发出工具调用。
> 真正有信息量的是它**转而做了什么**。

这是很好的科研素养示范。我以后自己设计对照组要抄这个习惯：
**先问这条结论是被实验测出来的，还是被实验设置直接蕴含的。**

---

## 待办

- [ ] guarded 组跑 N 次，看「约束能否消除编造」——验证正文那句「只能降低概率」
- [ ] 换一个模型（deepseek）重跑五组，看 `no_reasoning` 的结论是否随模型改变
- [ ] 我自己那版 `agent/` 的第 6 组对照：工具定义留着但把 description 改成空/误导，看选型和传参
