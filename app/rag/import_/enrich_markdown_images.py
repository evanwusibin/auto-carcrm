from pathlib import Path
import re
from typing import List, Dict

import stem
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.infra.object_stroage.minio_gateway import minio_gateway
from app.process.import_.agent.state import ImportGraphState
from app.shared.runtime.logger import logger, step_log



from app.infra.llm.providers import llm_provider
from app.shared.runtime.load_prompt import load_prompt
import base64
import mimetypes
from minio.deleteobjects import DeleteObject

from app.shared.utils.rate_limit_utils import apply_api_rate_limit


# **函数签名**: `load_markdown_and_image_dir(state: dict) -> tuple[str, Path, Path]`
#             **步骤**
#             1. 读取 `md_content` 和 `md_path`
#             2. 校验 `md_path` 是否为空
#             3. 如果 `md_content` 为空，则按 `md_path` 读取文件正文
#             4. 拼接图片目录 `images`
#             5. 返回正文、Markdown 路径和图片目录路径
# D:\heimaAI\PytorchSDXX\08_掌柜智库\ai_0302_knowledge_base\app\rag\import_\enrich_markdown_images.py 我觉得今天老师教的这个还是比较简单的逻辑诶，可能老师还没有敲完，一个方法是用于加载存储md的路径一个是存储md_content内容，第一个方法主要是在state中取到两个属性，md_path和md_content 判断是不是空的，也就是后续测试验证的时候要传入的内容，不是空的就使用Path方法转为字典对象，md_content不需要转，因为直接是读取md_path转字典，使用read_text读取你买了的文本内容就行。然后定义一个images_path_ob字段来拼接一个images的路径，最后将这三个返回，md_path_obj,一个是从一个里面取出来放到md_content 的文本内容，一个是从md_path_obj拼接到的一个images路径
# 然后就是定义scan_images方法，先设置一个空容器存储上下文[]，函数输入就是md_content.image_path_obj,然后假设需要查看上下文昌都市100个字符，输出格式就是元祖，第一个参数是图片名称，图片路径，里面包了一一个上文和下文内容。然后遍历image_path_obj子目录下的所有文件，取名字，如果文件后缀不是属于图片就警告，如果是的话那就通过正则匹配一下输出图片再全文中的开始和结束的位置，用search返回结果中有一个span，如果没有知道啊就跳过被，然后就是从match中渠道start和end，取到上文和下文，切片的方法，将md_content切开，start前面100个字符的位置到start就是图片前的上文，下午问以此类推，但是需要考虑极端情况，所以还是哟啊用max和min，最后返回的内容按照输出格式报一下，image_context(str,str,tuple(str,str))
@step_log("load_markdown_and_image_dir")
def load_markdown_and_image_dir(state: ImportGraphState) -> tuple[str,Path,Path]:
    # 1、获取参数 md_content md_path  转对象
    md_path = state["md_path"]
    md_content = state["md_content"]
    # 2、md_path 非空校验
    if not md_path:
        logger.error("md_path为空,无法获取图片地址等,业务无法继续!")
        raise ValueError("md_path为空,无法获取图片地址等,业务无法继续!")
    # 3、md_content 继续非空校验/空给与默认值
    md_path_obj:Path = Path(md_path)
    if not md_content:
        # zip用bytes  文本用text
        logger.info(f"md_content没有内容,可能从md数据格式过来的!根据md_path二次读取即可!")
        md_content = md_path_obj.read_text(encoding="utf-8")
        if not md_content:
            logger.error(f"{md_path}读取markdown_content内容失败,业务无法继续执行")
            raise ValueError(f"{md_path}读取markdown_content内容失败,业务无法继续执行")

    # 4、images 对应path获取
    images_path_obj = md_path_obj.parent / 'images'
    # 5、返回结果
    return md_content,md_path_obj,images_path_obj


SUPPORTED_IMAGE_EXTENSIONS =  {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
def scan_images(md_content:str, image_path_obj:Path,content_length:int = 100) -> List[tuple[str, str, tuple[str,str]]]:
    # 1、从image_path_obj中获取每一个文件
    image_context = []
    # 遍历目录下的所有文件和子目录 iterdir
    for image_file_obj in image_path_obj.iterdir():
        image_name = image_file_obj.name
        # 判断是不是图片
        if not image_file_obj.suffix in SUPPORTED_IMAGE_EXTENSIONS:
            # 不是图片
            logger.warning(f"文件{image_name}不是一张图片，无需处理跳过本次循环")
            continue
        #2、定义这张图片专属的正则
        # ！[]（名字）  escape高数正则不存在特殊符号  再包一层避免关键字
        reg = re.compile(r"\!\[.*?\]\(.*?"+re.escape(image_name)+r".*?\)")
        match= reg.search(md_content)

        # 3、match校验，不存在是图片达拉斯没有应用
        if not match:
            logger.warning(f"图片{image_name}没有被md内容应用无需处理，跳过本次循环")
            continue

        # 4、mat中的定位获取上下文数据 str[:]
        start,end = match.span()   # match  . star()  end()
        pre_content = md_content[max(start-content_length,0):start]  # 如果start-context 小于0 就是0
        post_content = md_content[end:min(end+content_length,len(md_content))]    # end_context >len(max)  -> max
        # 这个元祖的形状对应 tuple[str,str,tuple[str,str]]
        image_context.append(
            (
                image_name,
                str(image_file_obj),
                (
                pre_content,
                post_content
                )
            )
        )
    logger.info(f"完成了图片上下文提取{image_context}")
    return image_context
# 3. 获取图片的上下文 参数: md_content image_path_obj , context_length:int = 100 响应: list[tuple[str,str,tuple[str,str]]]
#             scan_images
#             [ (图片名 erdaye.png , c:/xxx/erdaye.png, (上文,下文))  ,  , , , , ]
#             思路: 从图片文件夹中获取每张图片! 拿这单张图片去md_content中匹配! 匹配到了! 返回对应位置  start - context_length  end + context_length
#             1. 从imgae_path_obj中获取每一个文件
#             2. 遍历循环 -> 文件判断 -> 是不是图片
#             3. 定义这张图片专属的正则规则
#             4. 使用正则在md_content中进行匹配 search 有 只有一个 或者没有
#             5. 没有 -> md_content没有被引用不用识别上下文!
#             6. 有 -> 获取start | end 截取上下文
#             7. 填装数据
#             8. 返回即可
@step_log("summarize_images")
def summarize_images(images_context_list:list[tuple[str, str, tuple[str, str]]], stem: str ) -> Dict[str,str]:
    """
    继续图片意图识别
    :param images_context: 图片名称 地址 上下文
    :param md_path: 图片所在文件夹
    :return: {图片和对应的含义}
    """
    # 1、获取视觉模型对象 llm   providers  vision_chat
    # 注意修改LLMProvider 添加实例化  llm_provider = LLMProvider()
    vision_model = llm_provider.vision_chat()
    # 2、准备  图片 图片描述
    images_summary_dict: Dict[str,str] = {}
    # 3、循环 -> (图片名，，地址，（上，下）) in  [(图片名，，地址，（上，下）)]
    for image_name,image_path,(pre_content,post_content) in images_context_list:
        # 4、加载提示词  后面两个key是固定的
        # 添加访问限制 等待休眠，超出数量就休眠
        apply_api_rate_limit()
        # 加载提示词  来自runtime里面的方法  后面两个参数是固定的
        image_summary_prompt = load_prompt("image_summary", root_folder=stem, image_content = (pre_content, post_content))
        # 图片
        # 图片  1、传到minio http 开头网络地址  公网
        # 2、图片转base64字符串  文件-> base64字符串  base64.b64encode(文件.read_bytes())  原始直接转为base64处理的直接    .decode("utf-8") 转成base64字符串
        # 3、base字符串  ->  原始的字节数据
        #   base64.b64decoder(base6字符串)  -> bytes  固定写法
        image_path_obj = Path(image_path)
        # base64.b64encode(文件.read_bytes()).decode("utf-8") 固定写法  里面一定要是文件对象
        image_base_str = base64.b64encode(image_path_obj.read_bytes()).decode("utf-8")
        # 前文传递数据结构，列表中两个字典
        human_message = HumanMessage(
            content = [
                {
                    # 放图片内容  固定写法
                    "type": "image_url",
                    # 图片具体内容  http地址  base64
                    # minmetype类型
                    "image_url": {
                        # 返回字典取第一个
                        "url": f"data:{mimetypes.guess_type(image_name)[0]};base64,{image_base_str}"
                    },
                },
                # 图片对应的辅助描述  固定写法
                {"type": "text", "text": f"f{image_summary_prompt}"},
            ]
        )
        # 5、和视觉模型继续交互  普通写法
        # response = vision_model.invoke(human_message)
        # response.content
        
        #chain   链式调用
        vision_chains = vision_model | StrOutputParser()
        # 执行的时候是message列表，规定的必须[]  图片描述
        image_summary = vision_chains.invoke([human_message])
        # 6、存储到对应字典中
        images_summary_dict[image_name] = image_summary
    logger.info(f"完成图片识别 -识别处理结果为{images_summary_dict}")
    return images_summary_dict

# 图片描述，
@step_log("upload_images_and_replace")
def upload_images_and_replace(image_context_list: list[tuple[str, str, tuple[str, str]]], image_summaries_dict: Dict[str, str], md_content: str, stem: str) -> str:
    # 1、删除原文件子啊minio存储的图片信息
    # 2、循环传递每一张图片minio的服务器
    # 3、存储每张图片对应的minio的网络地址
    # {image_name:url}
    # {image_name:描述}
    # 4、循环处理每一张图片替换md_content
    # 5、返回新的md_content
    """
        进行minio的文件上传和md_content 内容替换
    :param image_context_list: {(图片名称，地址，（上，下）)】
    :param image_summaries_dict: {图片名称：描述}
    :param md_content: md内容！[]（./）
    :param stem: 烫金机
    :return: 新的 md_content
    """
    # 1、输出原我家在minio中存储的图片信息
    """
        存储图片的路径 object_name
            image_dir -> 所有图片的刚刚前缀
                stem -> 对应每个文件的文件夹方便继续文件输出和查看
                    image_name.jpg  -> 具体的文件
    """
    # 1、先查询  list_object 想要查询的对象列表
    # todo minio的gateway 实例化一个对象
    # 固定的填写方法
    list_object = minio_gateway.client().list_objects(
        bucket_name=minio_gateway.bucket_name,
        # 查询不到 前面多了 / [1:]  取第一个后面的内容
        prefix=f"{minio_gateway.image_dir[1:]}/{stem}",  # 删除指定文件夹对应的图片
        recursive=True
    )
    delete_object_list = [ DeleteObject(lo.object_name) for lo in list_object ]
    # 1.2 根据对象列表进行删除
    # 里面是一个yield  里面一个查询一个删除  里面是一个生成器需要固定返回一个errors迭代执行
    errors = minio_gateway.client().remove_objects(
        bucket_name=minio_gateway.bucket_name,
        delete_object_list=delete_object_list
    )
    for error in errors:
        logger.warning(f"输出文件出现异常！{error}")
    logger.info(f"已经删除完成了！！！")

    # 2、循环 传递每一张图片到minio服务器
    image_minio_url_dict:Dict[str,str] = {}
    for image_name,image_path_str,_ in image_context_list:
        # fput_object(bucket_name, object_name, file_path, content_type=”application/octet-stream”, metadata=None,
        # fput_object
        try:
            object_name = f"{minio_gateway.image_dir}/{stem}/{image_name}"
            minio_gateway.client().fput_object(
                bucket_name=minio_gateway.bucket_name,
                # 固定的前缀 、 文件名称  图片名称
                object_name=object_name,
                file_path=image_path_str,
                content_type=mimetypes.guess_type(image_name)[0]
            )
            # 3、 存储每张图片对应的minio的网络地址
            image_minio_url_dict[image_name] = minio_gateway.build_image_url(stem,image_name)
        except Exception as e:
            logger.warning(f"{image_name}的图片上传失败！{e} 跳过继续上传！")
    #    {image_name:url}
    #    {image_name:描述}
    # 4. 循环处理每一张图片,替换md_content内容
    for image_name,image_ur in image_minio_url_dict.items():
        # image_name -> image_ur
        # image_name -> image_summary
        image_summary = image_summaries_dict[image_name]
        # md_content提供
        # 正则 sub("要替换入内容",md_content)
        # ![](image_name) -> ![image_summary](image_ur)
        # md_content 提供
        # 正则替换 sub(“要替换如内容”,md_content)
        reg = re.compile(r"\!\[.*?\]\(.*?"+re.escape(image_name)+r".*?\)")
        # 替换
        # 参数1: 要替换入的内容 1. 替换入的字符 [会解析 /分组符号]  2. 匿名函数 lambda 只是调用一次函数,返回结果 他不在处理!!
        # 参数2: 在哪个文本中替换
        # 每次替换完,返回一个替换后的新内容
        # image_summary  | image_url 存在分组符号 /2 /1   ![{image_summary}]({image_ur}) -> 找到我对应的一个匹配项
        # ![{image_summary}]({image_ur}) -> 1   2   -> 匹配项只有一个 出现异常
        # 避免特殊字符串
        md_content = reg.sub(lambda _ : f"![{image_summary}]({image_ur})",md_content)
    return md_content

@step_log("back_up_new_md_content")
def back_up_new_md_content(md_content_new, md_path_obj):
    """
    新的md——content内容备份
    :param md_content_new:内
    :param md_path_obj: 源地址 _new.md
    :return: 新的字符串地址
    """
    # 新的地址 Path
    new_md_path_obj = md_path_obj.with_name(f"{md_path_obj.stem}_new.md")
    # 写出数据即可
    new_md_path_obj.write_text(md_content_new,encoding="utf-8")
    return str(new_md_path_obj)

@step_log("enrich_markdown_images")
def enrich_markdown_images(state:ImportGraphState) -> ImportGraphState:
        """
        Markdown 图片增强服务：
        1. 扫描 Markdown 中的图片
        2. 调用多模态模型生成图片说明
        3. 上传图片到 MinIO
        4. 替换 Markdown 图片地址并回写 md_content
        """
        # 1、获取操作参数 md_content  md_path_obj  images_path_obj  加载 md 内容和图片目录
        md_content,md_path_obj,image_path_obj = load_markdown_and_image_dir(state)
        # 2、判断image_path 是否存在内容，没有，直接进入下一行节点，没有推按也一定有images
        if not any(image_path_obj.iterdir()):
            # 空文件夹
            logger.warning(f"当前{md_content}没有图片，无需图片处理，正常进入下一个节点")
            return state

        # List[tuple[str,str,tuple[str,str]]] [(图片名.jpg,图片完整地址,(上文,下文))]
        # 3、识别md_content 图片上下文  扫描图片，拿到每个图片的上下文
        images_context: List[tuple[str, str, tuple[str, str]]] = scan_images(md_content, image_path_obj)
        # return state

         # 4、图片信息通过vision模型继续识别含义：
         #    方法(scan_images的返回值（图片名，地址，（上，下）），md_path_obj.stem 文件夹名称) -> 字典[str 图片名字.png,str 图片描述]
         #    1、获取视觉模型对象 llm/providers vision_chat
         #    2、准备一个存储含义的字典 images_dict  [str,str] = {}
         #    3、循环 -> （图片名，地址，（上，下）），md_path_obj.stem 文件夹名称) in [(图片名，地址,(上，下))]
         #    4、拼接模型对提示词
         #    5、想模型发起请求chains  结果解析器   str_output_parser
         #    6、结果封装到 字典中 图片名  ： 图片描述
         #    7、直接返回字典即可
        # [图片，图片描述]
        # 4、使用视觉模型对图片继续意图识别
        # {图片.png :描述}   调多模态 LLM 生成图片描述
        images_summary_dict = summarize_images(images_context, md_path_obj.stem)

        # 5、上传图片并替换md_content  上传图片到 MinIO + 替换 md 里的图片地址
        md_content_new = upload_images_and_replace(images_context,images_summary_dict,md_content,md_path_obj.stem)

        # 6、备份新的md_content_new -> md_path_obj  烫金机.md  烫金机_new.md   备份新 md 文件 → 烫金机_new.md
        new_md_path_str = back_up_new_md_content(md_content_new,md_path_obj)
        # 7、更新state md_content  md_path
        state["md_content"] = md_content_new
        state["md_path"] = new_md_path_str
        # 8、返回结果
        return state











