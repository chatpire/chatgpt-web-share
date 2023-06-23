from typing import Any


class SelfDefinedException(Exception):
    def __init__(self, reason: Any = None, message: str = "", code: int = -1) -> None:
        self.reason = reason  # 异常主要原因
        self.message = message  # 更细节的描述
        self.code = code    # 错误码：-1 为默认；0～1000 以内正数为 http 错误码；10000 以上为自定义错误码

    def __str__(self):
        return f"{self.__class__.__name__}: [{self.code}] {self.reason} {self.message}"


class AuthenticationFailedException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.authenticationFailed", message=message, code=10401)


class AuthorityDenyException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.authorityDeny", message=message, code=10403)


class UserNotExistException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.userNotExist", message=message)


class UserAlreadyExists(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.userAlreadyExists", message=message)


class InvalidParamsException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.invalidParams", message=message)


class ResourceNotFoundException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.resourceNotFound", message=message)


class InvalidRequestException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.invalidRequest", message=message)


class InternalException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.internal", message=message)


class ConfigException(SelfDefinedException):
    def __init__(self, message: str = ""):
        super().__init__(reason="errors.config", message=message)


class OpenaiException(SelfDefinedException):
    def __init__(self, reason: str, message: str = "", code: int = -1):
        super().__init__(reason=reason, message=message, code=code)


class OpenaiWebException(OpenaiException):
    def __init__(self, message: str = "", code: int = -1):
        super().__init__(reason="errors.openaiWeb", message=message, code=code)


class OpenaiApiException(OpenaiException):
    def __init__(self, message: str = "", code: int = -1):
        super().__init__(reason="errors.openaiWeb", message=message, code=code)
