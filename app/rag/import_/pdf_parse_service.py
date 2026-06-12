import os
import shutil
import time
import requests

from app.process.import_.agent.state import ImportGraphState, create_default_state
from pathlib import Path
from app.rag.import_.config import MINERU_MODEL_VERSION, MINERU_POLL_TIMEOUT_SECONDS, MINERU_POLL_INTERVAL_SECONDS
from app.shared.runtime.logger import logger, PROJECT_ROOT, step_log
from app.infra.config.providers import infra_config

"""
PDF 解析服务：
1. 调用 MinerU
2. 下载并解压解析结果
3. 获取 Markdown 路径和正文内容
4. 回写 md_path / md_content / local_dir

md_path
md_content

节点步骤分析:

validate_pdf_paths(state:ImportGraphState) -> tuple[Path pdf_path_obj, Path local_dir_path_obj]
1.获取local_dir /pdf_path
2.进行参数校验local_dir/pdf_path

upload_pdf_and_poll
3.向minerU申请上传文件地址
4.向minerU返回的预签名地址上传文件
5.使用batch_id轮询获取返回结果

download_and_extract_markdown
6.通过zipurl地址下载指定文件
7.进行文件的解压full.md
8.md重新命名问题


9.更新state数据 md_path  md_content

10.返回state [增量]

"""

# 1、pdf  dir路径校验和完善
@step_log("validate_pdf_path")
def validate_pdf_path(state:ImportGraphState)->tuple[Path,Path]:
    """
    :param state:
    :return:
    """
    # 1、读取 pdf_path   local_dir
    pdf_path = state.get("pdf_path")
    local_dir = state.get("local_dir")
    # 2、校验 pdf_path  是否为空
    if not pdf_path:
        logger.error(f"进行pdf转化md，但是pdf_path解析为空，无法继续解析")
        raise ValueError("进行pdf转化md，但是pdf_path解析为空，无法继续解析")
    # 3、 若 local_dir 为空  则写入默认输出目录
    if not local_dir:
        logger.warning(f"进行pdf转化md，但是发现local_dir为空，我们给与默认值 项目 、output")
        local_dir = PROJECT_ROOT / "output"    # Path
    # 4、转换为 path对象
    pdf_path_obj = Path(pdf_path)  # 后续对文件存在性校验更方便
    local_dir_obj = Path(local_dir)   # 这块不报错 Path可以报Path
    # 5、校验PDF是否存在
    if not pdf_path_obj.exists():
        logger.error(f"进行PDF转md，但是{pdf_path}，但是不存在文件，业务无法继续")
        raise FileNotFoundError(f"进行PDF转md，但是{pdf_path}，但是不存在文件，业务无法继续")
    # 6、若输出目录不存在自动创建
    if not local_dir_obj.exists():
        logger.warning(f"继续pdf转md，local_dir值{local_dir_obj}，但是没有这个文件夹，我们自行创建")
        # exist_ok = True 当存在的时候不会创建也不会报错
        local_dir_obj.mkdir(parents=True,exist_ok=True)
    # 7、 返回  pdf_path_obj  lcoal_dir_obj
    # 一个输入一个输出的位置
    return pdf_path_obj,local_dir_obj



#upload_pdf_and_poll(pdf_path_obj:Path)  - str
#1、校验MinerU 配置是否完整
#2、调用 file-url、batch  申请上传地址与  batch_id
#3、使用 Session(trust_env = False) 上传PDF文件
#4、根据 batch_id 轮训任务状态
#5、若任务成功 返回full_zip_url
#6、若任务失败或超时，抛出异常
@step_log("upload_pdf_and_poll")
def upload_pdf_and_poll(pdf_path_obj:Path)->str :
    """
    上传PDF文件到MinerU服务，并轮询等待解析完成，最终返回解析结果的下载地址
    :param pdf_path_obj: 本地PDF文件路径对象
    :return: 解析完成后的ZIP压缩包下载地址
    """
    if not infra_config.mineru.base_url or not infra_config.mineru.api_key:
        logger.error(f"minerU请求核心参数为空baseUrl或者API，业务无法继续进行")
        raise ValueError(f"minerU请求核心参数为空baseUrl或者API，业务无法继续进行")
    # 2、调用 file_urls   batch   申请上传地址与 batch_id
    token = infra_config.mineru.api_key
    url = f"{infra_config.mineru.base_url}/file-urls/batch"
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "files": [
            {"name": f"{pdf_path_obj.name}"}
        ],
        "model_version": MINERU_MODEL_VERSION
    }
    try:
        response = requests.post(url, headers=header, json=data,timeout= MINERU_POLL_TIMEOUT_SECONDS)
        # 状态码是否正常200(服务器状态)
        if response.status_code != 200:
            logger.error(f"服务器发生异常！无法继续业务处理响应状态码为{response.status_code}")
            raise RuntimeError(f"服务器发生异常！无法继续业务处理响应状态码为{response.status_code}")

        # 判断业务是否正常0（业务状态）
        response_dict = response.json()
        code = response.json().get("code")
        if code != 0:
            logger.error(f"业务处理发生异常，业务状态码为{code},异常信息：{response_dict.get('msg')}")
            raise RuntimeError(f"业务处理发生异常，业务状态码为{code},异常信息：{response_dict.get('msg')}")

        batch_id = response_dict.get("data",{}).get("batch_id")
        upload_file_url = response_dict.get("data",{}).get("file_urls")[0]
        logger.info(f"调用‘ / file-urls / batch申请上传地址与batch_id  batch_id: {batch_id}, 上传地址: {upload_file_url}")

    except Exception as e:
        logger.error(f"向minerU申请上传文件地址发生异常url参数{url}，key参数{token}")
        raise e

    # 3、获取请求会话  Session(trust_env = False ) 上传PDF文件
    try:
        with requests.Session() as session:
            session.trust_env = False  # put就是放上去的意思   把pdf读取成二进制文件
            # 1、resuest.session（）获取请求会话
            # session 使用和requests是一样的
            # 作用：1、可以服用请求 requests.Session()  session.get post session.close()
            #  作用2： 有些特殊设置trust_env  = False  我谁也不信
            put_responses = session.put(upload_file_url,data=pdf_path_obj.read_bytes())
            # status_code | code
            if put_responses.status_code != 200:
                logger.error(f"向地址：{upload_file_url}上传文件发生异常，状态码为{put_responses.status_code}")
                raise RuntimeError(f"向地址：{upload_file_url}上传文件发生异常，状态码为{put_responses.status_code}")
            # status_code | code  网络状态和业务状态
    except Exception as e:
        logger.error(f"想minerU申请上传文件一直发生异常url参数{str(e)}")
        raise e


    # 4、 根据 batch_id  轮训任务状态
    # 前置准备工作
    get_zip_url = f"{infra_config.mineru.base_url}/extract-results/batch/{batch_id}"
    timeout = MINERU_POLL_TIMEOUT_SECONDS
    interval_time = MINERU_POLL_INTERVAL_SECONDS
    start_time = time.time()

    while True:
        # 获取结果 抛出异常 timeout
        # 1、先判定是否超时
        if time.time() - start_time > timeout:
            logger.error(f"轮训获取请求结果超时！用时{time.time() - start_time}")
            raise TimeoutError(f"轮训获取请求结果超时！用时{time.time() - start_time}")
        # 2、发起网络请求（报错，再给一次机会）
        try:
            get_response = requests.get(get_zip_url, headers=header)

        except Exception as e:
            logger.warning(f"获取下载的zip的URL地址网络请求失败，等待后继续尝试")
            time.sleep(interval_time)
            continue  # continue（跳出此次循环）  break（跳出循环）

        # 3、判断也u我状态码 status_code
        # 客户端  ->  服务端 -> 1 2 3 4 5
        if get_response.status_code != 200:
            # 一定是错误了，看这个错误给机会   5xx
            if 500 <= get_response.status_code < 600:
                # 给机会
                logger.warning("获取下载的zip地址，mineru对应的服务器异常，状态码{get_response.status_code}")
                time.sleep(interval_time + 2)
                continue
            logger.error(f"获取下载的zip地址，mineru对应的服务器异常，状态码{get_response.status_code}业务无法继续了")
            raise RuntimeError(f"获取下载的zip地址，mineru对应的服务器异常，状态码{get_response.status_code}业务无法继续了")

        # 4、判断code
        get_response_dict = get_response.json()
        if get_response_dict.get("code") != 0:
            logger.error(f"获取下载的zip地址，mineru对应的服务器异常，状态码{get_response_dict.get("code")},错误信息：{get_response_dict.get('msg')},业务无法继续了")
            raise RuntimeError(f"获取下载的zip地址，mineru对应的服务器异常，状态码{get_response_dict.get("code")},错误信息：{get_response_dict.get('msg')},业务无法继续了")

        # 5、获取结果信息（是否解析完毕） 正在解析  循环 解析完毕 获取结果  return 解析失败 抛出异常
        result_dict = get_response_dict.get("data", {}).get("extract_result", [])[0]
        result_state = result_dict.get("state", "failed")

        if result_state == "done":
            full_zip_url = result_dict.get("full_zip_url")
            if not full_zip_url:
                # 下载地址是空 任务失败 → 抛出异常
                logger.error(f"获取下载的zip地址，mineru对应的下载zip的地址是空的，状态码业务无法继续了")
                raise RuntimeError(f"获取下载的zip地址，mineru对应的下载zip的地址是空的，状态码业务无法继续了")
            return full_zip_url
        if result_state == "failed":
            # 下载地址空 任务失败 → 抛出异常
            logger.error(f"获取下载的zip地址，mineru对应的下载地址是空的，解析失败了，状态码业务无法继续了")
            raise RuntimeError(f"获取下载的zip地址，mineru对应的下载地址是空的，解析失败了，状态码业务无法继续了")
        # 正在解析中.... 任务仍在处理中 → 等待后继续轮询
        logger.warning(f"{pdf_path_obj.name}minerU正在解析中..............")
        time.sleep(interval_time)

#这一层有三个关键点：
#
# 1. **先拿上传地址，再传文件**: 不是直接把 PDF 传给业务接口，而是先通过 MinerU 申请预签名上传地址。
# 2. **PUT 上传要用 `Session(trust_env=False)`**: 这样可以绕开系统代理，避免预签名 URL 被污染导致上传失败。
# 3. **轮询参数不写死在函数里**: `timeout`、`interval_time`、`model_version` 全部走配置常量，后期调优更方便。
#
# 总结：为什么 PUT 这里需要 `Session(trust_env=False)`？
#
# 1. `POST / GET` 一般是普通业务接口：
#    它们主要校验地址、参数和认证信息，通常不会像预签名上传那样对请求细节做严格签名校验。
# 2. `PUT` 这里对应的是预签名 URL 上传：
#    它使用的是对象存储直传地址，签名校验更严格。
#    - 如果请求经过系统代理，代理可能会追加或改写部分请求头，导致签名校验失败。
#    - 设置 `Session(trust_env=False)` 后，可以绕过系统代理环境变量，尽量保持上传请求原样发送。

@step_log("download_and_extract_markdown")
def download_and_extract_markdown(zip_url:str, local_dir_path_obj:Path, stem: str) -> Path:
    """
     下载 MinerU 解析完成的 ZIP 压缩包，解压并提取出标准的 MD 文件
     1. 从 zip_url 下载解析结果压缩包
     2. 解压到指定目录
     3. 自动查找最合适的 MD 文件（优先同名 → full.md → 第一个）
     4. 重命名为统一规范的文件名并返回

     Args:
         zip_url: MinerU 返回的 ZIP 下载地址
         local_dir_path_obj: 本地存放解压文件的目录
         stem: 原始 PDF 的文件名（不带后缀，用于重命名 MD）

     Returns:
         Path: 最终整理好的 MD 文件路径对象
     """
    # ---------------------- 1. 下载 ZIP 压缩包 ----------------------
    # 发送请求下载解析好的 ZIP 文件
    response = requests.get(zip_url, timeout=MINERU_POLL_TIMEOUT_SECONDS)
    # 拼接 ZIP 保存路径：输出目录 + 文件名_result.zip
    zip_path_obj = local_dir_path_obj / f"{stem}_result.zip"
    # 将二进制内容写入 ZIP 文件  text  content  josn  前两个有property没有变量的，后面是有限量
    zip_path_obj.write_bytes(response.content)
    # ---------------------- 2. 解压 ZIP 文件 ----------------------
    # 解压目录 = 输出目录 / PDF 文件名（无后缀）
    extract_path_obj = local_dir_path_obj / stem
    # 如果解压目录已存在，先删除（防止旧文件干扰）  也可以用 .is_dir() 判断是否文件夹文件夹是否有效
    if extract_path_obj.is_dir():
        shutil.rmtree(extract_path_obj)
    # 创建新的解压目录
    extract_path_obj.mkdir(parents=True, exist_ok=True)
    # 解压 ZIP 包到目标目录
    shutil.unpack_archive(zip_path_obj, extract_path_obj)
    # ---------------------- 3. 查找所有 MD 文件 ----------------------
    # 递归查找解压目录下所有 .md 文件  全局搜索  glob  rglob 建议用第二个  返回yield 生成器 ，需要循环读取
    md_file_list = list(extract_path_obj.rglob("*.md"))
    # 没有找到 MD 文件则抛出异常  any  任何一个   一个都没有  或者 or len(md_file_list) ==0
    if not any(md_file_list):
        logger.error(f"下载地址：{zip_url},下载成功，解压后发现没有任何md文件，业务无法继续进行！！！")
        raise FileNotFoundError(f"文件解压失败，在{extract_path_obj}没有任何md文件")

    # ---------------------- 4. 按优先级选择 MD 文件 ----------------------
    # 优先级 1：找和 PDF 同名的 MD（最标准）
    for md_file in md_file_list:
        # 解压的文件名和本地的文件名一样
        if md_file.stem == stem:
            logger.info(f"解压的文件名称就是源文件名，无需二次修改：{md_file.name}")
            return md_file
    # 优先级 2：找不到同名，找 full.md（MinerU 默认完整导出文件）
    target_md_obj = None
    for md_file in md_file_list:
        if md_file.name.lower() == "full.md": # 有一个这样的名字，就需要重命名了
            target_md_obj = md_file
            break
    # 优先级 3：还找不到，直接取第一个 MD
    if not target_md_obj:
        target_md_obj = md_file_list[0]
    # ---------------------- 5. 重命名为统一规范名称 ----------------------
    # 将选中的 MD 重命名为 {stem}.md（和 PDF 同名）
    # rename（目标名） 重命名  并且会修改裁判文件名称  with_name()获取修改名称但不改变磁盘  with_stem不会修改磁盘
    # rename(新的地址)  target_md_obj  改成目标path  修改磁盘
    return target_md_obj.rename(target_md_obj.with_stem(f"{stem}.md"))



    # token = "官网申请的api token"
    # batch_id = "上一步批提交返回的batch_id"
    # url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
    # header = {
    #     "Content-Type": "application/json",
    #     "Authorization": f"Bearer {token}"
    # }
    # res = requests.get(url,headers=header)
    # print(res.status_code)
    # print(res.json())
    # print(res.json()["data"])

    # 5、若任务成功  返回  full_zip_url
    # 6、 若任务失败或超时 抛出异常

@step_log("parse_pdf_to_markdown")
def parse_pdf_to_markdown(state: ImportGraphState) -> ImportGraphState:
    """
    PDF 解析服务：
    1. 调用 MinerU
    2. 下载并解压解析结果
    3. 获取 Markdown 路径和正文内容
    4. 回写 md_path / md_content / local_dir
    :param state:
    :return:
    """
    # 先校验 PDF 路径和输出目录，避免把非法输入送进解析服务。
    pdf_path_obj, local_dir_path_obj = validate_pdf_path(state)
    # 上传 PDF 到 MinerU，并轮询直到服务端返回最终压缩包地址。
    zip_url = upload_pdf_and_poll(pdf_path_obj)
    logger.info(f"minerU返回的zip地址:{zip_url}")
    # 下载结果包并提取最终 Markdown 文件。
    md_path_obj = download_and_extract_markdown(zip_url, local_dir_path_obj, pdf_path_obj.stem)
    # 修改主图状态
    state["md_path"] = str(md_path_obj)
    state["md_content"] = md_path_obj.read_text(encoding="utf-8")
    return state


if __name__ == "__main__":
        from app.process.import_.agent.nodes.node_pdf_to_md import node_pdf_to_md
        logger.info("===== 开始 node_pdf_to_md 节点联调测试 =====")

        test_pdf_path = os.path.join(PROJECT_ROOT, "doc", "hak180使用说明书.pdf")
        test_state = create_default_state(
            task_id="test_pdf2md_task_001",
            pdf_path=test_pdf_path,
            local_dir=os.path.join(PROJECT_ROOT, "output"),
        )

        result = node_pdf_to_md(test_state)
        logger.info(f"md_path: {result['md_path']}")
        logger.info(f"md_content长度: {len(result['md_content'])}")
        logger.info("===== 结束 node_pdf_to_md 节点联调测试 =====")