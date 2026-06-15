# -*- coding: utf-8 -*-
import re
import base64
import mimetypes
from pathlib import Path
from typing import List, Dict

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from minio.deleteobjects import DeleteObject

from app.infra.llm.providers import llm_provider
from app.infra.object_stroage.minio_gateway import minio_gateway
from app.process.import_.agent.state import ImportGraphState
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger, step_log
from app.shared.utils.rate_limit_utils import apply_api_rate_limit


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


@step_log("load_markdown_and_image_dir")
def load_markdown_and_image_dir(state: ImportGraphState) -> tuple[str, Path, Path]:
    md_path = state["md_path"]
    md_content = state["md_content"]
    if not md_path:
        raise ValueError("md_path为空，无法获取图片地址")
    md_path_obj = Path(md_path)
    if not md_content:
        md_content = md_path_obj.read_text(encoding="utf-8")
        if not md_content:
            raise ValueError(f"读取md内容失败: {md_path}")
    images_path_obj = md_path_obj.parent / "images"
    return md_content, md_path_obj, images_path_obj


@step_log("scan_images")
def scan_images(md_content: str, image_path_obj: Path, content_length: int = 100) -> List[tuple[str, str, tuple[str, str]]]:
    image_context = []
    if not image_path_obj.exists():
        return image_context
    for image_file_obj in image_path_obj.iterdir():
        image_name = image_file_obj.name
        if image_file_obj.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        reg = re.compile(r"\!\[.*?\]\(.*?" + re.escape(image_name) + r".*?\)")
        match = reg.search(md_content)
        if not match:
            continue
            # 提取上图片的前后坐标
        start, end = match.span()
        pre_content = md_content[max(start - content_length, 0):start]
        post_content = md_content[end:min(end + content_length, len(md_content))]
        image_context.append((image_name, str(image_file_obj), (pre_content, post_content)))
    logger.info(f"扫描到 {len(image_context)} 张图片")
    return image_context


@step_log("summarize_images")
def summarize_images(images_context_list: List[tuple[str, str, tuple[str, str]]], stem: str) -> Dict[str, str]:
    vision_model = llm_provider.vision_chat()
    if not vision_model:
        logger.warning("视觉模型未启用，跳过图片识别")
        return {}

    images_summary_dict: Dict[str, str] = {}
    for image_name, image_path, (pre_content, post_content) in images_context_list:
        apply_api_rate_limit()
        image_summary_prompt = load_prompt("image_summary", root_folder=stem, image_content=(pre_content, post_content))
        image_path_obj = Path(image_path)
        image_base_str = base64.b64encode(image_path_obj.read_bytes()).decode("utf-8")
        human_message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mimetypes.guess_type(image_name)[0]};base64,{image_base_str}"
                    },
                },
                {"type": "text", "text": image_summary_prompt},
            ]
        )
        vision_chain = vision_model | StrOutputParser()
        image_summary = vision_chain.invoke([human_message])
        images_summary_dict[image_name] = image_summary
    logger.info(f"完成图片识别，共 {len(images_summary_dict)} 张")
    return images_summary_dict


@step_log("upload_images_and_replace")
def upload_images_and_replace(
    image_context_list: List[tuple[str, str, tuple[str, str]]],
    image_summaries_dict: Dict[str, str],
    md_content: str,
    stem: str,
) -> str:
    list_object = minio_gateway.client().list_objects(
        bucket_name=minio_gateway.bucket_name,
        prefix=f"{minio_gateway.image_dir[1:]}/{stem}",
        recursive=True,
    )
    delete_object_list = [DeleteObject(lo.object_name) for lo in list_object]
    errors = minio_gateway.client().remove_objects(
        bucket_name=minio_gateway.bucket_name,
        delete_object_list=delete_object_list,
    )
    # minio必须要递归删除
    for error in errors:
        logger.warning(f"删除MinIO旧图片异常: {error}")

    image_minio_url_dict: Dict[str, str] = {}
    for image_name, image_path_str, _ in image_context_list:
        try:
            object_name = f"{minio_gateway.image_dir}/{stem}/{image_name}"
            minio_gateway.client().fput_object(
                bucket_name=minio_gateway.bucket_name,
                object_name=object_name,
                file_path=image_path_str,
                content_type=mimetypes.guess_type(image_name)[0],
            )
            image_minio_url_dict[image_name] = minio_gateway.build_image_url(stem, image_name)
        except Exception as e:
            logger.warning(f"{image_name} 上传MinIO失败: {e}，跳过")

    for image_name, image_url in image_minio_url_dict.items():
        image_summary = image_summaries_dict.get(image_name, image_name)
        reg = re.compile(r"\!\[.*?\]\(.*?" + re.escape(image_name) + r".*?\)")
        md_content = reg.sub(lambda _: f"![{image_summary}]({image_url})", md_content)

    return md_content


@step_log("back_up_new_md_content")
# 先建一个文件然后再文件中写入数据 ，用with_name  write_text
def back_up_new_md_content(md_content_new: str, md_path_obj: Path) -> str:
    new_md_path_obj = md_path_obj.with_name(f"{md_path_obj.stem}_new.md")
    new_md_path_obj.write_text(md_content_new, encoding="utf-8")
    return str(new_md_path_obj)


@step_log("enrich_markdown_images")
def enrich_markdown_images(state: ImportGraphState) -> ImportGraphState:
    md_content, md_path_obj, image_path_obj = load_markdown_and_image_dir(state)

    if not image_path_obj.exists() or not any(image_path_obj.iterdir()):
        logger.warning("当前文档没有图片，跳过图片增强")
        return state

    images_context = scan_images(md_content, image_path_obj)
    if not images_context:
        logger.warning("未扫描到被引用的图片，跳过图片增强")
        return state

    images_summary_dict = summarize_images(images_context, md_path_obj.stem)
    md_content_new = upload_images_and_replace(images_context, images_summary_dict, md_content, md_path_obj.stem)
    new_md_path_str = back_up_new_md_content(md_content_new, md_path_obj)

    state["md_content"] = md_content_new
    state["md_path"] = new_md_path_str
    return state
