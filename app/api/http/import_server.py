"""
导入服务 HTTP 入口模块，直接承载导入接口与相关接口业务逻辑。
"""
import shutil
import sys
import uuid
from datetime import datetime
from mimetypes import guess_type
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.schemas.import_schema import TaskStatusSchema, UploadSchema
from app.shared.runtime.logger import PROJECT_ROOT, logger
from app.process.import_.agent.main_graph import kb_import_app
from app.process.import_.agent.state import get_default_state, ImportGraphState, create_default_state
from app.infra.config.providers import settings
from app.shared.utils.task_utils import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_PROCESSING,
    get_done_task_list,
    get_running_task_list,
    get_task_status,
    update_task_status, add_running_task, add_done_task,
)

app = FastAPI(
    title=settings.import_app_name,
    description="企业化 RAG 导入服务，负责文件上传、导入执行与状态查询。",
    version="0.2.0",
)

# 跨域问题 同源策略
app.add_middleware(
    # 前端解决：配置代理  后端解决：配置请求头和请求体等
    CORSMiddleware,
    allow_origins=list(settings.cors_origins) or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/html")
def html():
    html_path_obj = PROJECT_ROOT / "app" / "resources" / "html" / "import.html"
    return FileResponse(
        path = html_path_obj,
        media_type =guess_type(html_path_obj.name)[0]
    )

# 2、返回task_id的任务状态
@app.get("/status/{task_id}")
def task_status(task_id:str):
    logger.info(f"获取任务状态接口被调用，task_id:{task_id}")
    return TaskStatusSchema(
        code = 200,
        task_id = task_id,
        status = get_task_status(task_id),
        done_list = get_done_task_list(task_id),
        running_list = get_running_task_list(task_id),
    )


def invoke_graph(task_id:str,local_file_path:Path,local_dir:Path):
    """
    调用图对象 .invoke
    :param task_id:
    :param local_file_path_obj:
    :param local_dir:
    :return:
    """
    state = create_default_state(task_id=task_id,local_file_path=str(local_file_path),local_dir=str(local_dir))

    try:
        #
        logger.info(f"{task_id}对应的文件解析任务开始执行！ 参数state：{state}")
        update_task_status(task_id,TASK_STATUS_PROCESSING)
        final_state = kb_import_app.invoke(state)
        logger.info(f"{task_id}对应的文件解析已经完成，最终结果为{final_state}")
        update_task_status(task_id,TASK_STATUS_COMPLETED)
    except Exception as e:
        update_task_status(task_id,TASK_STATUS_FAILED)
        logger.exception(f"=====================全流程测试运行失败========================")


# 3、上传文件的异步接口 post   upload  files   文件列表  后台执行图过程
@app.post('/upload')
def upload_and_invoke_graph(background_tasks: BackgroundTasks, files:list[UploadFile]) :
    """
    1、接受上传的文件  存储到项目下
    2、异步执行导入图对象  state   lcoal_file_path lcoal_dir  sask_id
    3、直接返回结果
    :param background_tasks:
    :return:
    """
    # 约定存储的位置 /output  /  时间 / task_id  ->  local_dir  +  文件名.pdf  -> local_file_path
    # 1.1 接受上传的文件（文件存储到项目下）
    # 准备一个存储文件夹（没有task_id）
    task_id = str(uuid.uuid4())  # 永远不重复的随机字符串
    local_dir_path_obj = PROJECT_ROOT / 'output' / datetime.now().strftime("%Y%m%d%H%M%S") / task_id
    # 没有给我建一个 非空判断
    local_dir_path_obj.mkdir(parents=True, exist_ok=True)

    # 1.2 将文件存储文件夹中
    current_file = files[0]
    local_file_path_obj = local_dir_path_obj / current_file.filename

    # 写入
    # # ❌ 直接 read() → 小文件可以，大文件可能内存爆炸
    with local_file_path_obj.open('wb') as file_buffer:
        ##copyfileobj好处:
        #流式读取:一次只读一小段(默认 64KB)
        #读完一段写一段，循环直到写完
        # 内存永远只占用 64KB，不管文件多大
        #速度极快，系统底层优化
        #不会阻塞服务器，支持高并发
        # 自带缓冲区，不用自己处理
        # current_fildfile

        #copyfileobj → 循环读取 64KB，边读边写，不占内存
        shutil.copyfileobj(current_file.file, file_buffer)

    # 2、异步调用图，蓝图解析 local_file_path_obj  local_dir_path_obj  task_id
    background_tasks.add_task(
        # FastAPI 的 add_task 签名是 add_task(func, *args, **kwargs)，第一个位置参数必须是函数，不能用 invoke_graph=invoke_graph。
        invoke_graph,
        task_id = task_id,
        local_file_path = local_file_path_obj,
        local_dir= local_dir_path_obj,
    )
    return UploadSchema(
        code = 200,
        message = "文件上传成功！",
        task_ids = [task_id]
    )


if __name__ == "__main__":
    # 一句话：任何 Web 框架保存上传文件，核心都是"打开本地文件 → 把上传内容写进去"，写法基本固定。
    # 唯一区别是框架不同时获取文件对象的方式不同，但写入这步都一样 👍
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.import_app_port)





























