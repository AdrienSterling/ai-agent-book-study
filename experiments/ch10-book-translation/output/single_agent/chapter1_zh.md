# 第1章：LLM推理基础

大型语言模型在能够对任何内容进行推理之前，首先要把文本转化为数字。每一段文本首先被拆分为一个**词元（token）**，这是模型所处理的最小单元。然后每个词元被映射为一个**嵌入（embedding）**，即一个在高维空间中捕捉其含义的稠密向量。

当用户发送一个请求时，他们所写的文本被称为**提示词（prompt）**。在该提示词上运行模型以生成回答的过程被称为**推理（inference）**。从发送提示词到收到第一个响应之间的时间，就是用户直接感受到的**延迟（latency）**。

一次最简推理调用如下所示：

```python
def generate(prompt: str, model) -> str:
    tokens = model.tokenize(prompt)      # split prompt into tokens
    embeddings = model.embed(tokens)     # map each token to an embedding
    output = model.forward(embeddings)   # run inference
    return model.detokenize(output)
```

有两个数字主导着用户体验。第一，提示词中的词元数量，因为提示词越长，计算成本越高。第二，首个词元的延迟，因为首个词元响应缓慢会让整个系统感觉迟钝。在本书中，我们会反复回到这些概念：词元、嵌入、提示词、推理和延迟。现在就把它们的定义弄清楚，可以避免日后的困惑。