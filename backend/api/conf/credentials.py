from typing import Optional

from pydantic import BaseModel

from api.conf.base_config import BaseConfig
from utils.common import SingletonMeta

_TYPE_CHECKING = False


class CredentialsModel(BaseModel):
    openai_web_access_token: Optional[str] = None
    # chatgpt_account_username: Optional[str] = None
    # chatgpt_account_password: Optional[str] = None
    openai_api_key: Optional[str] = None


class Credentials(BaseConfig[CredentialsModel], metaclass=SingletonMeta):
    if _TYPE_CHECKING:
        openai_web_access_token: Optional[str]
        # chatgpt_account_username: Optional[str]
        # chatgpt_account_password: Optional[str]
        openai_api_key: Optional[str]

    def __init__(self, load_config: bool = True):
        super().__init__(CredentialsModel, "credentials.yaml", load_config=load_config)
