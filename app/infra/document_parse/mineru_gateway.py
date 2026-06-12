from app.infra.config.providers import infra_config

class MinerUGateway:
    @property
    def base_url(self) -> str:
        """
         获取 MinerU 服务基础地址。

         Returns:
           str: MinerU 接口基础 URL。
        """
        return infra_config.mineru.base_url

    @property
    def api_key(self) -> str:
        """
         获取 MinerU 服务 API Token。

         Returns:
            str: MinerU 调用所需的 Token。
        """
        return infra_config.mineru.api_key

mineru_gateway = MinerUGateway()




# **这一层的定位**
#
# - `mineru_gateway.base_url` 对外提供 MinerU 服务地址
# - `mineru_gateway.api_key` 对外提供 MinerU 调用 Token
# - 当前这层以统一配置出口为主
# - 后续可以从“配置门面”继续扩展为“MinerU 交互门面”