# -*- coding: utf-8 -*-
import requests
import time
import zipfile
import os
from app.shared.config.mineru_config import mineru_config
from app.shared.runtime.logger import logger


class MinerUGateway:
    """MinerU 文档解析网关，负责 PDF 上传、轮询、下载。"""

    @property
    def base_url(self) -> str:
        return mineru_config.base_url

    @property
    def api_key(self) -> str:
        return mineru_config.api_key

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def upload_pdf(self, file_path: str) -> str:
        """上传 PDF 文件到 MinerU，返回 task_id。"""
        url = f"{self.base_url}/extract/task"
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.post(url, headers=headers, files=files, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        task_id = data.get("task_id") or data.get("data", {}).get("task_id")
        if not task_id:
            raise ValueError(f"MinerU 上传返回异常: {data}")
        logger.info(f"[MinerU] PDF 上传成功, task_id={task_id}")
        return task_id

    def poll_task(self, task_id: str, timeout: int = 600, interval: int = 3) -> dict:
        """轮询 MinerU 任务状态，直到完成或超时。"""
        url = f"{self.base_url}/extract/task/{task_id}"
        start = time.time()
        while time.time() - start < timeout:
            resp = requests.get(url, headers=self.headers, timeout=30)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            state = data.get("state", "")
            logger.info(f"[MinerU] task_id={task_id}, state={state}")
            if state in ("done", "completed", "success"):
                return data
            if state in ("failed", "error"):
                raise RuntimeError(f"MinerU 任务失败: {data}")
            time.sleep(interval)
        raise TimeoutError(f"MinerU 任务超时: task_id={task_id}")

    def download_result(self, download_url: str, save_dir: str) -> str:
        """下载 MinerU 解析结果 zip 并解压，返回解压目录。"""
        resp = requests.get(download_url, timeout=60)
        resp.raise_for_status()
        zip_path = os.path.join(save_dir, "mineru_result.zip")
        with open(zip_path, "wb") as f:
            f.write(resp.content)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(save_dir)
        os.remove(zip_path)
        logger.info(f"[MinerU] 结果已解压到 {save_dir}")
        return save_dir

    def extract_markdown(self, file_path: str, save_dir: str) -> str:
        """完整流程：上传 → 轮询 → 下载 → 返回 markdown 文件路径。"""
        task_id = self.upload_pdf(file_path)
        result = self.poll_task(task_id)
        download_url = result.get("download_url") or result.get("result", {}).get("download_url", "")
        if not download_url:
            raise ValueError(f"MinerU 返回结果中无 download_url: {result}")
        self.download_result(download_url, save_dir)
        md_files = [
            os.path.join(save_dir, f)
            for f in os.listdir(save_dir)
            if f.endswith(".md")
        ]
        if not md_files:
            raise FileNotFoundError(f"MinerU 解压后未找到 .md 文件: {save_dir}")
        return md_files[0]


mineru_gateway = MinerUGateway()
