# 第 3 章：优化推理时延

模型一旦能跑通，下一场战斗就是速度。目标是在提高**吞吐量**（系统每秒完成的请求数）的同时降低**时延**。这两者往往相互权衡。

最重要的技巧是 **KV 缓存**。在推理过程中，模型原本需要在每一步对之前所有词元重新计算注意力。通过缓存过去词元的键和值向量，模型只需处理最新的词元，从而大幅降低长提示词的时延。

```python
def decode_step(new_token, kv_cache):
    q, k, v = project(new_token)         # only the new token
    kv_cache.append(k, v)                # reuse past keys and values
    return attention(q, kv_cache.keys, kv_cache.values)
```

第二个技巧是**批处理**：将多个提示词分组在一起，让硬件保持忙碌。更大的批次能提高吞吐量，但可能损害单个请求的时延，因此服务系统会仔细调整批次大小。

结论是：推理性能是一种平衡。我们每避免重算一个词元，每做好一次提示词批处理，都会让系统同时朝着更低的时延和更高的吞吐量迈进。