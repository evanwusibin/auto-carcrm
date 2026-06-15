# node_05_item_name_recognition 主体识别

## 模块目的
识别文档的核心主体（如产品名称），并将其关联到每个切块。

## 流程图
```
输入：chunks, file_title
  ↓
1. 校验chunks非空
2. 拼接前K个chunk为上下文
3. 调用LLM识别主体名称
4. 回填item_name到每个chunk
5. 生成item_name向量
6. 存入Milvus
  ↓
输出：item_name, chunks(已回填)
```

## 对应service
item_name_service.py → recognize_and_index_item_name(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| `context = f'...'` | 每轮覆盖，只剩最后一片 | 用`+=`累加 |
| 只回写state不回写chunks | 下游读到None | 三步回填：state+chunks+写回state |
| LLM输出不稳定 | 识别结果为空 | file_title兜底 |
