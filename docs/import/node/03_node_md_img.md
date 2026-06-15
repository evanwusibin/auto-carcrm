# node_03_md_img 图片增强

## 模块目的
将MD中的图片上传到MinIO，替换为公网地址，并用Vision模型生成图片描述。

## 流程图
```
输入：md_path, md_content
  ↓
1. 加载MD内容和图片目录
2. 扫描图片并提取上下文
3. 调用Vision模型生成图片描述
4. 上传图片到MinIO并替换MD地址
5. 备份新MD文件
  ↓
输出：md_path(新), md_content(新)
```

## 对应service
enrich_markdown_images.py → enrich_markdown_images(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| re.escape(image_name) | 文件名中的`.`被当元字符 | 用re.escape转义 |
| match.span() | 返回的是(start,end)不是匹配内容 | start,end = match.span() |
| max(start-N, 0) | 上文截取越界 | 用max防越界 |
| base64编码 | 大图编码慢，占用内存 | 可选：先上传MinIO拿URL |
