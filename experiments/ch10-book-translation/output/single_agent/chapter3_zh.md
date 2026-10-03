# 第3章：优化推理延迟

一旦模型能够正常工作，下一场战斗就是速度。目标是在降低**延迟（latency）**的同时提高**吞吐量（throughput）**，即系统每秒完成的请求数量。这两者往往相互权衡。

最重要的技巧是**KV缓存（KV cache）**。在推理过程中，如果不使用缓存，模型在每一步都需要对所有先前的词元重新计算注意力。通过缓存过去词元的键（key）和值（value）向量，模型只需处理最新的词元，这为长提示词大幅削减了延迟。

```python
def decode_step(new_token, kv_cache):
    q, k, v = project(new_token)         # only the new token
    kv_cache.append(k, v)                # reuse past keys and values
    return attention(q, kv_cache.keys, kv_cache.values)
```

第二个技巧是**批处理（batching）**：将多个提示词分组在一起，使硬件保持忙碌。更大的批次能提高吞吐量，但可能损害任何单个请求的延迟，因此服务系统会仔细调整批次大小。

教训在于，推理性能是一种平衡。我们每避免重新计算一个词元，每将一个提示词批处理得当，都会同时推动系统朝着更低延迟和更高吞吐量的方向前进。