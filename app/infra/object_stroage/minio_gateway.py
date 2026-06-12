from langgraph.pregel import protocol
from minio import Minio

from app.shared.clients.minio_utils import get_minio_client
from app.infra.config.providers import infra_config


# 封装minio的gateway minio 对外提供属性方法的 ‘网关’
# 对外的属性： bucket_name  images_dir
# 对外的方法函数：client()   build_image_url()

def client():
    """获取 MinIO 客户端实例，用于上传、下载、查询文件等操作"""
    # minio_utils
    return get_minio_client()


class MinioGateway:
    """
    MinIO 对象存储网关类
    统一封装 MinIO 客户端获取、配置读取、图片URL拼接等能力，
    供全项目统一调用，避免到处写配置、重复拼接URL
    """

    # 注意： 这个方法之前交过，字典对象列表采用field，factoy啥的
    # bucket_name:str = infra_config.minio_bucket_name

    @property # 写了这个不需要初始化init
    def bucket_name(self):
        """获取 MinIO 存储桶名称（从全局配置读取）"""
        return infra_config.minio.bucket_name

    @property
    def image_dir(self):
        """获取 MinIO 中存放图片的目录路径（从全局配置读取）"""
        return infra_config.minio.minio_img_dir

    def client(self):
        # minio_utils
        return get_minio_client()

    def build_image_url(self, stem: str, object_name: str):
        # 桶
        # 文件名
        # 对象名
        #  协议 :// 端点:9000  / 桶 / minio_img_dir /  文件名 / 对象名
        protocol = "https" if infra_config.minio.minio_secure else "http"

        return (
            f"{protocol}://{infra_config.minio.endpoint}/{infra_config.minio.bucket_name}"
            f"{infra_config.minio.minio_img_dir}/{stem}/{object_name}"
        )
# 创建全局唯一的Minio网关实例
minio_gateway = MinioGateway()