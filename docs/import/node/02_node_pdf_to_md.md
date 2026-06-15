# node_02_pdf_to_md PDF转MD

## 模块目的
将PDF文件解析为Markdown格式，提取文本内容。

## 流程图
```
输入：pdf_path, local_dir
  ↓
1. 校验PDF路径
2. 上传PDF到MinerU解析服务
3. 轮询等待解析完成
4. 下载ZIP并解压
5. 选择MD文件
  ↓
输出：md_path, md_content
```

## 对应service
pdf_parse_service.py → parse_pdf_to_markdown(state)

## 与原项目差异
无变化，直接从原项目复制。

## 踩坑速查
| 坑 | 现象 | 解决 |
|----|------|------|
| Session(trust_env=False) | 代理污染预签名URL | 上传时绕过系统代理 |
| shutil.unpack_archive | 解压路径不存在 | 先创建目录 |
| rglob("*.md") | 找不到MD文件 | 检查解压是否成功 |
