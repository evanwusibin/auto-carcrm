# -*- coding: utf-8 -*-
import os
import shutil
import time
import requests

from app.process.import_.agent.state import ImportGraphState
from pathlib import Path
from app.rag.import_.config import MINERU_MODEL_VERSION, MINERU_POLL_TIMEOUT_SECONDS, MINERU_POLL_INTERVAL_SECONDS, MINERU_DOWNLOAD_TIMEOUT_SECONDS
from app.shared.runtime.logger import logger, PROJECT_ROOT, step_log
from app.infra.config.providers import infra_config


@step_log("validate_pdf_path")
def validate_pdf_path(state: ImportGraphState) -> tuple[Path, Path]:
    pdf_path = state.get("pdf_path")
    local_dir = state.get("local_dir")
    if not pdf_path:
        logger.error("进行pdf转化md，但是pdf_path解析为空，无法继续解析")
        raise ValueError("pdf_path解析为空，无法继续解析")
    if not local_dir:
        logger.warning("local_dir为空，使用默认输出目录 output")
        local_dir = PROJECT_ROOT / "output"
    pdf_path_obj = Path(pdf_path)
    local_dir_obj = Path(local_dir)
    if not pdf_path_obj.exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    if not local_dir_obj.exists():
        local_dir_obj.mkdir(parents=True, exist_ok=True)
    return pdf_path_obj, local_dir_obj


@step_log("upload_pdf_and_poll")
def upload_pdf_and_poll(pdf_path_obj: Path) -> str:
    if not infra_config.mineru.base_url or not infra_config.mineru.api_key:
        logger.error("MinerU配置不完整：base_url 或 api_key 为空")
        raise ValueError("MinerU配置不完整")

    token = infra_config.mineru.api_key
    url = f"{infra_config.mineru.base_url}/file-urls/batch"
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "files": [{"name": pdf_path_obj.name}],
        "model_version": MINERU_MODEL_VERSION
    }

    try:
        response = requests.post(url, headers=header, json=data, timeout=MINERU_POLL_TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise RuntimeError(f"MinerU申请上传地址失败，状态码: {response.status_code}")
        response_dict = response.json()
        if response_dict.get("code") != 0:
            raise RuntimeError(f"MinerU业务异常: {response_dict.get('msg')}")
        batch_id = response_dict.get("data", {}).get("batch_id")
        upload_file_url = response_dict.get("data", {}).get("file_urls")[0]
        logger.info(f"MinerU上传地址获取成功, batch_id: {batch_id}")
    except Exception as e:
        logger.error(f"向MinerU申请上传地址失败: {e}")
        raise

    try:
        with requests.Session() as session:
            session.trust_env = False
            put_response = session.put(upload_file_url, data=pdf_path_obj.read_bytes())
            if put_response.status_code != 200:
                raise RuntimeError(f"上传PDF到MinerU失败，状态码: {put_response.status_code}")
    except Exception as e:
        logger.error(f"上传PDF文件失败: {e}")
        raise

    get_zip_url = f"{infra_config.mineru.base_url}/extract-results/batch/{batch_id}"
    timeout = MINERU_POLL_TIMEOUT_SECONDS
    interval_time = MINERU_POLL_INTERVAL_SECONDS
    start_time = time.time()

    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError(f"MinerU轮询超时，已等待 {timeout} 秒")

        try:
            get_response = requests.get(get_zip_url, headers=header)
        except Exception:
            logger.warning("MinerU轮询请求失败，等待后重试")
            time.sleep(interval_time)
            continue

        if get_response.status_code != 200:
            if 500 <= get_response.status_code < 600:
                logger.warning(f"MinerU服务器异常，状态码: {get_response.status_code}，等待后重试")
                time.sleep(interval_time + 2)
                continue
            raise RuntimeError(f"MinerU返回异常状态码: {get_response.status_code}")

        get_response_dict = get_response.json()
        if get_response_dict.get("code") != 0:
            raise RuntimeError(f"MinerU业务异常: {get_response_dict.get('msg')}")

        result_dict = get_response_dict.get("data", {}).get("extract_result", [{}])[0]
        result_state = result_dict.get("state", "failed")
        err_msg = result_dict.get("err_msg", "")

        if result_state == "done":
            full_zip_url = result_dict.get("full_zip_url")
            if not full_zip_url:
                raise RuntimeError("MinerU解析完成但下载地址为空")
            return full_zip_url.strip("`").strip()
        if result_state == "failed":
            logger.error(f"MinerU解析失败详情: state={result_state}, err_msg={err_msg}")
            logger.error(f"MinerU完整响应: {get_response_dict}")
            raise RuntimeError(f"MinerU解析任务失败: {err_msg or '未知原因'}")

        logger.info(f"{pdf_path_obj.name} MinerU解析中... state={result_state}")
        time.sleep(interval_time)


@step_log("download_and_extract_markdown")
def download_and_extract_markdown(zip_url: str, local_dir_path_obj: Path, stem: str) -> Path:
    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.get(zip_url, timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)
                response.raise_for_status()
            break
        except Exception as e:
            logger.warning(f"下载 zip 失败(第{attempt+1}次): {e}")
            if attempt == max_retries - 1:
                raise RuntimeError(f"下载 MinerU 结果 zip 失败，已重试{max_retries}次: {e}")
            time.sleep(2)

    zip_path_obj = local_dir_path_obj / f"{stem}_result.zip"
    zip_path_obj.write_bytes(response.content)

    extract_path_obj = local_dir_path_obj / stem
    if extract_path_obj.is_dir():
        shutil.rmtree(extract_path_obj)
    extract_path_obj.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(zip_path_obj, extract_path_obj)

    md_file_list = list(extract_path_obj.rglob("*.md"))
    if not md_file_list:
        raise FileNotFoundError(f"解压后未找到任何md文件: {extract_path_obj}")

    for md_file in md_file_list:
        if md_file.stem == stem:
            logger.info(f"找到同名md文件: {md_file.name}")
            return md_file

    target_md_obj = None
    for md_file in md_file_list:
        if md_file.name.lower() == "full.md":
            target_md_obj = md_file
            break
    if not target_md_obj:
        target_md_obj = md_file_list[0]

    return target_md_obj.rename(target_md_obj.with_stem(f"{stem}.md"))


@step_log("parse_pdf_to_markdown")
def parse_pdf_to_markdown(state: ImportGraphState) -> ImportGraphState:
    pdf_path_obj, local_dir_path_obj = validate_pdf_path(state)
    zip_url = upload_pdf_and_poll(pdf_path_obj)
    logger.info(f"MinerU返回的zip地址: {zip_url}")
    md_path_obj = download_and_extract_markdown(zip_url, local_dir_path_obj, pdf_path_obj.stem)
    state["md_path"] = str(md_path_obj)
    state["md_content"] = md_path_obj.read_text(encoding="utf-8")
    return state


@step_log("parse_file_to_markdown")
def parse_file_to_markdown(state: ImportGraphState) -> ImportGraphState:
    """
    统一文件解析入口：根据文件后缀调用不同的解析方法
    支持格式：.pdf / .md / .txt / .docx / .xlsx / .csv
    """
    file_ext = state.get("file_ext", "").lower()
    local_file_path = state.get("local_file_path") or state.get("pdf_path")
    
    if not local_file_path:
        raise ValueError("local_file_path为空，无法继续解析")
    
    path_obj = Path(local_file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {local_file_path}")
    
    # 根据文件后缀选择解析方法
    if file_ext == ".pdf":
        # PDF走MinerU解析
        return parse_pdf_to_markdown(state)
    
    elif file_ext in [".md", ".txt"]:
        # MD和TXT直接读取
        md_content = path_obj.read_text(encoding="utf-8")
        state["md_path"] = local_file_path
        state["md_content"] = md_content
        logger.info(f"[parse_file] 直接读取{file_ext}文件，长度={len(md_content)}")
        return state
    
    elif file_ext == ".docx":
        # DOCX需要转换
        try:
            from docx import Document
            doc = Document(local_file_path)
            md_content = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            state["md_path"] = local_file_path
            state["md_content"] = md_content
            logger.info(f"[parse_file] DOCX解析完成，长度={len(md_content)}")
            return state
        except ImportError:
            logger.error("python-docx未安装，请运行: uv add python-docx")
            raise
    
    elif file_ext in [".xlsx", ".csv"]:
        # 表格文件转换为文本
        try:
            import pandas as pd
            if file_ext == ".xlsx":
                df = pd.read_excel(local_file_path)
            else:
                df = pd.read_csv(local_file_path)
            
            # 转换为文本格式（使用 to_string 代替 to_markdown，避免依赖 tabulate）
            md_content = f"# {path_obj.stem}\n\n"
            md_content += df.to_string(index=False)
            
            state["md_path"] = local_file_path
            state["md_content"] = md_content
            logger.info(f"[parse_file] {file_ext}解析完成，长度={len(md_content)}")
            return state
        except ImportError:
            logger.error("pandas未安装，请运行: uv add pandas openpyxl")
            raise
    
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")
