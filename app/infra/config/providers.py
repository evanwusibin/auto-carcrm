# # 把所有的配置，config 汇总在一起
# from FlagEmbedding.inference.reranker.model_mapping import RerankerConfig
# from agents.agent import MCPConfig
# from app.shared.config.embedding_config import embedding_config, EmbeddingConfig
# from app.shared.config.lm_config import lm_config, LLMConfig
# from app.shared.config.bailian_mcp_config import mcp_config
# from app.shared.config.milvus_config import milvus_config, MilvusConfig
# from app.shared.config.mineru_config import mineru_config, MinerUConfig
# from app.shared.config.minio_config import minio_config, MinIOConfig
# from app.shared.config.reranker_config import reranker_config
# from app.shared.config.settings_config import settings
#
# from dataclasses import dataclass , field
#
# @dataclass
# class InfraConfig:
#     # 属性名字 ：类型  = field 赋值（ 可变类型 对象  集合 字典 不能直接复制）
#     # app -> 函数default_factory   ->  函数返回值 两个地址
#     app: object = field(default_factory=lambda: settings)
#     llm: LLMConfig = field(default_factory=lambda: lm_config)
#     embedding: EmbeddingConfig = field(default_factory=lambda: embedding_config)
#     reranker: RerankerConfig = field(default_factory=lambda: reranker_config)
#     mcp: MCPConfig = field(default_factory=lambda: mcp_config)
#     milvus: MilvusConfig = field(default_factory=lambda: milvus_config)
#     mineru: MinerUConfig = field(default_factory=lambda: mineru_config)
#     minio: MinIOConfig = field(default_factory=lambda: minio_config)
#
#     # 不可变类型 字符  数字 bool
#     #  = 赋值
#     #  = filed（default = 值）  直接赋值常量就行可以通过
#
# infra_config = InfraConfig()
# print(infra_config.llm.import_app_name)
# from app.shared.config.embedding_config import embedding_config

# 怎么解决的!
# 可以 先用一个  default =
# 属性:数字 字符 串bool = 默认值
# 字典 列表 对象 =filed(default_factory=lambda :x)

from app.shared.config.embedding_config import embedding_config,EmbeddingConfig
from app.shared.config.lm_config import lm_config,LLMConfig
from app.shared.config.bailian_mcp_config import mcp_config,McpConfig
from app.shared.config.milvus_config import milvus_config,MilvusConfig
from app.shared.config.mineru_config import mineru_config,MinerUConfig
from app.shared.config.minio_config import minio_config,MinIOConfig
from app.shared.config.settings_config import settings
from app.shared.config.reranker_config import  reranker_config,RerankerConfig

from dataclasses import dataclass ,field
@dataclass
class InfraConfig:
    # 属性名: 类型 =  可变类型 对象 集合 字典等等 不能直接赋值
    # app -> 函数(default_factory) ->  函数的返回值 两个地址
    app: object = field(default_factory = lambda :settings)
    llm: LLMConfig = field(default_factory = lambda: lm_config)
    embedding: EmbeddingConfig = field(default_factory = lambda: embedding_config)
    reranker: RerankerConfig = field(default_factory = lambda: reranker_config)
    mcp: McpConfig = field(default_factory = lambda:mcp_config)
    milvus: MilvusConfig = field(default_factory = lambda:milvus_config)
    mineru: MinerUConfig = field(default_factory = lambda:mineru_config)
    minio: MinIOConfig = field(default_factory = lambda: minio_config)
    # 不可变类型 字符 数字 bool
    #  = 赋值
    #  = field(default = 值 )
    # name:str = "wusibin"
    # field(default_factory=lambda: settings)

infra_config = InfraConfig()
