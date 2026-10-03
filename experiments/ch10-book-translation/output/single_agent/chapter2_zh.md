# 第2章：Transformer与注意力机制

现代语言模型建立在**Transformer**架构之上。其核心思想是**注意力（attention）**：模型不是严格从左到右地读取序列，而是让每个词元都能查看其他所有词元，并决定哪些词元更重要。这正是Transformer能够将代词与出现在许多词元之前的名词关联起来的原因。

注意力作用于每个词元的**嵌入（embedding）**。对于每个词元，模型计算三个向量——查询（query）、键（key）和值（value）——并用它们来权衡每个词元应该对其他词元投入多少注意力。

```python
def attention(query, key, value):
    scores = query @ key.T          # similarity between tokens
    weights = softmax(scores)       # attention weights
    return weights @ value          # weighted embedding
```

由于注意力会将每个词元与其他所有词元进行比较，随着提示词变长，其成本会迅速增长。这就是我们将在下一章中着手解决的延迟问题的根本原因。尽管如此，注意力正是赋予Transformer强大能力的关键：在推理过程中，它让模型能够灵活地在整个提示词范围内路由信息，而不是通过一条固定的流水线。