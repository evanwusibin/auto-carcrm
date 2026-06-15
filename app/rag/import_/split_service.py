import json
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.process.import_.agent.state import ImportGraphState
from app.rag.import_.config import CHUNK_OVERLAP, CHUNK_MAX_SIZE,CHUNK_SIZE
from app.shared.runtime.logger import logger, step_log


def _read_text_auto_encoding(file_path: Path) -> str:
    """
    自动检测文件编码并读取文本内容
    支持 UTF-8、GBK、GB2312、GB18030、Big5 等常见编码
    """
    # 尝试的编码列表（按优先级排序）
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1']
    
    for encoding in encodings:
        try:
            content = file_path.read_text(encoding=encoding)
            logger.info(f"[编码检测] 成功使用 {encoding} 编码读取文件: {file_path.name}")
            return content
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # 如果所有编码都失败，使用 latin-1（不会失败，但可能显示乱码）
    logger.warning(f"[编码检测] 所有编码尝试失败，使用 latin-1 兜底: {file_path.name}")
    return file_path.read_text(encoding='latin-1')


@step_log("load_markdown_content")
def load_markdown_content(state:ImportGraphState)-> tuple[str, str,Path]:
    """
     从状态字典中安全加载 Markdown 内容和文档标题
    1. 优先从 state 中直接读取
    2. 缺失时自动从文件读取兜底
    3. 统一换行符格式，保证文本干净
    :return: (处理后的md内容, 文件标题)
    :param state:
    :return:
    """
    # 1、获取三个变量 content  md_path  file_title  字典取值最好用state.get("")从状态中获取核心数据
    content = state.get("content")
    md_path= state.get("md_path")
    file_title = state.get("file_title")
    md_path_obj = Path(md_path)
    # 判空 如果状态中没有md内容，尝试从本地md文件读取（兜底逻辑）
    if not content:
        logger.warning("没有从state读取到content内容，我们使用md_path尝试再次读取！！！")
        # 如果文件路径存在，则读取文件内容
        if md_path:
            # "content 为空 → 按 md_path 读取文件（支持多种编码）
            content = _read_text_auto_encoding(md_path_obj)
            # 读完就state赋值
            state["content"] = content
        # 二次判断 双重校验，仍然邬内容，直接抛出异常终止流程
        if not content:
            # 如果还是空的就直接报错
            logger.error(f"md_path为空无法继续")
            raise ValueError(f"content中没数据，md_path为空无法继续")
    # 判断file_title是否为空 实现定义好了Path(md_path)对象 直接取名字就好了，不为空
    if not file_title:
        # 如果为空就直接从路径中提取文件名称就行赋值
        file_title = md_path_obj.stem if md_path_obj else "default"
        state["file_title"] = file_title
    # 统一替换符号，清洗数据
    # 最后再统一返回
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return content,file_title,md_path_obj


# 根据语义切割
@step_log("split_by_titles")
def split_by_titles(content: str, file_title: str) -> list[dict]:
    # 先定义一个正则 匹配是不是标题行
    reg = re.compile(r"^\s*#{1,6}\s.+")
    # 然后每一行用\n切开隔开
    lines = content.split("\n")
    # 初始化变量 存储最终切块的结果 当前正在拼接的块标题，当前块的所有行内容，
    chunks,current_title,current_lines,chunk_size,is_code_block = [],"",[],0,False
    for line in lines:
        # 循环遍历
        line = line.strip()
        # 空行跳过
        if not line:
            logger.warning("处理行为空行，跳过本次循环")
            continue
        if (line.startswith("```") or line.startswith("~~~")):
                is_code_block = not is_code_block
                # 继续新的一行
                current_lines.append(line)
                continue
        if(reg.match(line) and not is_code_block):
            # 阶段 如果匹配正则是正确的并且 不是在代码块中 就存入快中
            if current_title and len(current_lines) > 1:
                chunks.append({
                    "file_title": file_title,
                    "title":current_title,
                    "content":"\n".join(current_lines)
                })
                # 已经结算过一次了累加1结算上一次
                chunk_size +=1
            # 结算之后，就开启新的块，重新赋值 将当前读取的line赋值，代表上一个快结束了
            current_title = line
            current_lines = [line]
        else:
            # 不是标题切不是代码块的普通行，就直接逐行追加
            current_lines.append(line)
    # 最后一个没办法遇到下一个标题触发阶段，只能跳出循环直接固定做最后䘣的结算
    if current_title and len(current_lines) > 1:
        chunks.append({
            "file_title": file_title,
            "title": current_title,
            "content": "\n".join(current_lines)
        })
        chunk_size +=1
    # 兜底 全文无标题时
    if chunk_size == 0:
        chunks.append({
            "file_title": file_title,
            "title": "default",
            "content": content
        })
    logger.info(f"完成文档语义切割，共计切出：{chunk_size}块！ 切块内容：{chunks}")
    return chunks


@step_log("_split_long_chunk")
def _split_long_chunk(chunk:dict, max_length:int = CHUNK_MAX_SIZE) -> list[dict]:
    """
    你的理解	✅
    把过长的块切小	✅ 主作用对了
    大于 1000 字符才切	✅ 触发条件（> CHUNK_MAX_SIZE）
    用 list 存放	✅ 返回 list[dict]
    每个 chu

    nk 里有很多属性	✅ title/parent_title/part/file_title/content
    :param chunk:
    :param max_length:
    :return:
    """
    content = chunk.get("content")
    title = chunk.get("title")
    body = content
    if content.startswith(title):
        body = content[len(title):].lstrip()
    # 2、定义每块的固定前缀和块的有小长度
    prefix = title + "\n"
    available_length = max_length - len(prefix)
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n ", "\n", "。", "!","?"],  # 字符集切割
        chunk_size=available_length,
        chunk_overlap=CHUNK_OVERLAP
    )
    sub_chunks = []
    for index, chunk_content in enumerate(splitter.split_text(body), start=1):
        content = chunk_content.strip()
        if not content:
            continue

        full_content = (prefix + content).strip()

        sub_chunks.append({
            "content":full_content,
            "title": f"{title}-{index}" if title else f"chunk-{index}",
            "parent_title": title,
            "part": index,
            "file_title":chunk["file_title"],
        })
    logger.info(f"已经切割完成了")
    return sub_chunks


@step_log("_merge_short_chunks")
def _merge_short_chunks(final_chunks,min_length:int = CHUNK_SIZE,max_length:int = CHUNK_MAX_SIZE) -> list[dict]:
    # 1、申明一个最终数据集合 final_merge_chunks = []
    # 2、定义一个其实的指正 start = chunk = None
    # 3、循环要和并的列表 final_chunks  要合的下一个next_chunk
    #     for next_chunk[下一个] in final_chunk:
            # 第一次 start_chunk = 第一个值
            # 4、if not star_chunk:
                # start_chunk = next_chunk
                # continue
            # 第二次 satrt_chunk 要合并入的chunk[往这个里面合并 判断他的长度]
            #     next_chunk  要合并如的chunk [第二个指针]
            # 5、判断 start_chunk 的长度 < 600  and start_chunk['parent_title'] == next_chunk["parent_title"]
                # if start_chunk 的长度问题 < 600 and star_chunk[...]
                # 6、满足可以继续合并吧
    # 1、声明合并后的列表结果
    final_merge_chunks = []
    # 2、记录第一个指正chunk的位置
    start_chunk = None
    # 3、循环处理后续的chunk继续合并处理
    for next_chunk in final_chunks:
        # 第一次
        # 4、start_chunk 没有复制 把第一个复制
        if not start_chunk:
            start_chunk = next_chunk
            continue
        # 第二次之后
        # 5、start content 是否小于600 and next 是不是同一个父标题
        is_lt_chunk_size = len(start_chunk.get('content')) < min_length
        is_same_parent_title = start_chunk.get('parent_title') and start_chunk.get("parent_title") == next_chunk.get("parent_title")
        if is_lt_chunk_size and is_same_parent_title:
            # 截取标题后的内容
            # 同一个父标题 star长度小于600 再判断合并长度 标题/内容  如果有两个父标题以及快小于600，就把二次切的那个标题去掉，拼接再第一个starr的内容后面
            next_content_to_title = next_chunk.get('content')[len(next_chunk.get("parent_title")):]
            start_content = start_chunk.get("content")
            # 7、长度校验
            merge_content = start_content + "\n" + next_content_to_title
            if len(merge_content) <= max_length:
                start_chunk['content'] = merge_content
                logger.info(f"父标题:{start_chunk['parent_title']}, start: {start_chunk['title']}  next: {next_chunk['title']} 完成合并!!")
            else:
                # start_chunk 合不进 next_chunk → 先存 start_chunk，再让 next_chunk 成为新的 start_chunk，继续往后看。
                # 当前这个merge已经大于1000，合不进了，只能新开一个merge
                final_merge_chunks.append(start_chunk)
                start_chunk = next_chunk
                continue
        else:
            final_merge_chunks.append(start_chunk)
            start_chunk = next_chunk
    # 循环完毕了
    if start_chunk:
        final_merge_chunks.append(start_chunk)
    return final_merge_chunks

@step_log("refine_chunks")
def refine_chunks(chunks:list[dict],max_len:int = CHUNK_MAX_SIZE,min_len:int = CHUNK_SIZE) -> list[dict]:
    """
     进行精细切割,一共分为三步! 长切 / 短合 / 补全属性
    :param chunks: 原始内容
    :param max_len: 触发长切参数
    :param min_len: 触发短合参数
    :return: 最终处理后的chunk
    """
    # 定义接收最终的结果
    final_chunks = []
    # 1、循环判断是否需要长切
    for chunk in chunks:
        if len(chunk['content']) > max_len:
            # 拆分过长的块，并加入结果列表
            long_chunks = _split_long_chunk(chunk, max_len)
            final_chunks.extend(long_chunks)  # 列表平铺，
        else:
            final_chunks.append(chunk)  # 字典整个加
    # 短合并
    final_merge_chunks = _merge_short_chunks(final_chunks)
    # 3、优化属性存在
    for chunk in final_merge_chunks:
        if "parent_title" not in chunk:
            chunk["parent_title"]  = chunk['title']
        if "part" not in chunk:
            chunk["part"] = 1
    # 4、返回处理后的结果
    return final_merge_chunks

    """
    3. 微精细切割处理 (chunks) -> final_chunks {title,content,file_title,parent_title,part}
    refine_chunks(chunks:list[dict[title ##xxx,content #xxxn/容\n内容,file_title 文名]], max_Length:int, min length:int)
        return chunks: list[dict[title #xx | #xx_1 ,file_title,content [只在一个语义下, 长度 600-1000],parent_title,part #xx,part 1 2 ]]
        final_chunks = []
    3.1判断 content有没有超长 1000->二次切割 同一个标题
        1、长切短
        条件  content >1000
        3.3.1  for chunk in chunks：
            3.1.2 if（len(chunk[content]）  > 1000 )  判断后
                3.1.3 继进行短切  langchian的递归切割器  逐层切
                long_chunks = _split_long_chunk(chunk)  ->  chunk   -> list[chunk,chunk]
                1、content格式的清理和有效长度计算
                    #title \n  line  \n   line  \n  line
                    切割的内容 body = content[len(title):]  拼接  \n  line  \n   line  \n  line
                2、每块的固定前缀  快的有效长度
                    prefix = title + \n\n
                             小块的内容
                    available_length = max_length - len(prefix)
                3、 定义递归切割器
                    splitter = ResursiveCharacterTextSplitter（
                                spearators = ["/n/n ","/n","。" ,"!"], # 字符集切割
                                chunk_size = available_length,
                                chunk_overlap = 常量 <- config.py
                                ）
                4、切割循环处理每一快
                    for index, chunk_content -> enu文本内容  in  splitter.splite_text(body)
                        sub_chunks.appen(
                    {
                        content:prefix + chunk_content,
                        title:chuck[title]_index
                        file_title:chunk[file_title]
                        parent_title:chunk[parent_title]
                        part:index
                    }
                )
                5、 返回 sub_chunks  return
                final_chunks.extends(long_chunks)    # 列表平铺列表只能用extends  不能用 append
            else:
                final_chunks.extends(chunks)

    3.2判断 content有没有超短 600->二次合并 同一个标题
        场景： 统一标题 内容小于600，同一个标题且有多个chunk
        final_chunks = _merge_short_chunks(final_chunks)  往短了合并后的 -> list[dict,dict,dict]
    3.3 兜底 part parent_title 默认值4.做数据备份处理 chunks ->chunk.json
        parent_title  part  一定有值吗？   -> 长  -> 短了切
        parent_title part一定有值么? -> 长->短切割了
        for chunk in final_chunks:
            if "parent_title" not in chunk:
                chunk[parent_title] = chunk[title]
            if "part" not in chunk:
                chunk[part] = 1
        return final_chunks

    5.更新state[chunks] = chunks
    :return:
    """
@step_log("backup_chunks_json")
def backup_chunks_json(final_chunks,md_path_obj):
    """
    数据备份 字典 -> 文件名.json
    :param final_chunks:
    :param stem:
    :return:
     """
    # 获取文件对象
    json_path_ob = md_path_obj.parent / f"{md_path_obj.stem}.json"
    # 写出内容即可.json 就是个字符串 固定写法
    json_path_ob.write_text(json.dumps(final_chunks,indent=4,ensure_ascii=False),encoding='utf-8')
    logger.info(f"完成数据备份，备份的位置：{str(json_path_ob)}")

def split_document(state: ImportGraphState) -> ImportGraphState:
    """
    文档切分服务：
    1. 按标题层级做一级粗切
    2. 对超长文本做二次细切
    3. 构造 chunks 列表
    4. 回写 chunks
    """
    """
    文档切块核心节点（RAG 最关键步骤）
    功能：加载增强后的 Markdown 内容 → 按标题智能切块 → 优化块大小 → 备份切块结果 → 写入状态
    输出：将分块后的文本列表存入 state，供后续向量化、入库使用
    
    文档切块核心节点（RAG 最关键步骤）
    功能：加载增强后的 Markdown 内容 → 按标题智能切块 → 优化块大小 → 备份切块结果 → 写入状态
    输出：将分块后的文本列表存入 state，供后续向量化、入库使用
    """

    # 1、从状态中加兹安【增强后的markdown内容】 和 【文档标题】
    content,file_title,md_path_obj = load_markdown_content(state)
    # 2、按照 markdown 标题（#，##，###）继续【智能语义切块】（保持段落完整性）
    chunks = split_by_titles(content,file_title)
    # 3、精细切割（设计长切合短切处理，返回最终处理的chunks）
    final_chunks = refine_chunks(chunks)
    # 备份final_chunks_json（final_chunks,md_path_obj）
    backup_chunks_json(final_chunks,md_path_obj)
    state["chunks"] = final_chunks
    return state



# 定义测试函数
if __name__ == '__main__':
    from app.shared.utils.path_util import PROJECT_ROOT
    # 切词的逻辑需要传入文档内容和md文件名称
    # 文件名称直接取路径非后缀
    # 内容直接读取路径字典中的text字典对象方法读取对象
    md_path = PROJECT_ROOT / "output" / "hak180使用说明书" / "hak180使用说明书.md"
    content = md_path.read_text(encoding="utf-8")
    result = split_by_titles(content, md_path.stem)

    print(f"\n共切出 {len(result)} 个 Chunk：")
    for i, chunk in enumerate(result, 1):
        print(f"\n{'─'*40}")
        print(f"Chunk {i}:")
        print(f"  title   : {chunk['title']}")
        print(f"  content : {repr(chunk['content'][:300])}...")