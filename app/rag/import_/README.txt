[rag/import_] 导入服务层执行顺序说明

一、主执行顺序（对应知识导入主链路）
  01. entry_service.py
      - 入口服务
      - 作用：识别输入文件类型，决定走哪条导入链路

  02. pdf_parse_service.py
      - PDF 解析服务
      - 作用：将 PDF / 文档内容转成 Markdown 或可处理文本

  03. enrich_markdown_images.py
      - 图片增强服务
      - 作用：处理 Markdown 中的图片内容，补充图片摘要或说明

  04. split_service.py
      - 文档切块服务
      - 作用：将长文档切成可检索的 chunks，并做切块优化与备份

  05. item_name_service.py
      - 主体识别服务
      - 作用：识别当前导入文档属于哪个主体/知识对象

  06. embedding_service.py
      - 向量化服务
      - 作用：为 chunks 生成 dense / sparse 混合向量

  07. index_service.py
      - 入库服务
      - 作用：将 chunks 写入 Milvus 向量库

  08. doc_meta_service.py
      - 元数据抽取服务
      - 作用：抽取车型、版本、日期、文档类型等结构化元数据

  09. knowledge_persist_service.py
      - 知识文档持久化服务
      - 作用：将知识文档主记录写入 MongoDB，并完成发布状态更新

二、配置与辅助文件
  - config.py
    - 导入链路相关配置（向量维度、字段长度等）

  - __init__.py
    - 包初始化文件

三、说明
  1. 上面顺序对应 app/process/import_/agent/main_graph.py 中的主执行链路。
  2. 实际节点名与 service 名不一定完全同名，但调用顺序基本一致。
  3. 如果后续新增 OCR、Excel 专项解析、图片专项理解等服务，请继续按顺序补编号说明。
