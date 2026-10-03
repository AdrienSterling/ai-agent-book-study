# 第4章：微调与部署

通用模型很少能开箱即用地适配某个具体产品。通常的解决办法是**微调（fine-tuning）**：在一个更小的、针对特定任务的数据集上继续训练模型，使其在保持通用能力的同时适应你的领域。

微调改变了模型将**提示词（prompt）**转化为答案的方式，但它并不改变基本的流水线：文本变成**词元（token）**，每个词元变成**嵌入（embedding）**，然后**推理（inference）**产生结果。改变的是模型所学习到的权重。

```python
def fine_tune(model, dataset):
    for prompt, target in dataset:
        loss = model.loss(prompt, target)   # compare output to target
        model.update(loss)                  # adjust weights
    return model
```

微调之后便是**部署（deployment）**：将模型封装在API之后，让真实用户能够发送提示词并获得答案。此时，前面提到的那些顾虑会以更大的力度重新浮现。延迟必须保持低位，吞吐量必须保持高位，而上一章介绍的KV缓存和批处理则承担了繁重的工作。

完整的旅程——词元、嵌入、提示词、推理、延迟、微调和部署——至此已经走完。一个曾经只是研究产物的模型，如今已经变成了人们真正可以使用的服务。