class KmsError(Exception):
    """KMS CLI 用户可见错误的基类。"""


class ConfigError(KmsError):
    """本地 CLI 配置缺失或无效时抛出。"""


class AuthError(KmsError):
    """认证信息缺失、过期或被拒绝时抛出。"""


class HttpRequestError(KmsError):
    """HTTP 请求在收到响应前失败时抛出。"""


class HttpStatusError(KmsError):
    """服务端返回非成功状态码时抛出。"""


class InvalidJsonError(KmsError):
    """服务端返回内容不是合法 JSON 时抛出。"""
