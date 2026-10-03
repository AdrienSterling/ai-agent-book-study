# 第 1 章：LLM 推理基础

大型语言模型在能够进行任何推理之前，首先要把文本转化为数字。每一段文本首先被切分为一个个**词元**，这是模型所处理的最小单位。随后，每个词元被映射为一个**嵌入向量**，即一个在高维空间中捕捉其含义的稠密向量。

当用户发送请求时，他们所写的文本被称为**提示词**。在该提示词上运行模型以生成回答的过程被称为**推理**。从发送提示词到收到第一个响应之间的时间，就是用户直接感受到的**时延**。

一次最简推理调用如下所示：

```python
def generate(prompt: str, model) -> str:
    tokens = model.tokenize(prompt)      # split prompt into tokens
    embeddings = model.embed(tokens)     # map each token to an embedding
    output = model.forward(embeddings)   # run inference
    return model.detokenize(output)
```

有两个数字主导着用户体验。第一，提示词中的词元数量，因为更长的提示词会消耗更多计算资源。第二，首个词元的时延，因为首个词元响应缓慢会让整个系统显得迟钝。在本书中，我们会反复回到这些概念：词元、嵌入向量、提示词、推理和时延。现在就把它们的定义弄清楚，可以避免后续产生混淆。