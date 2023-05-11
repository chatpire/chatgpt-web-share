from typing import Optional

from pydantic import BaseModel

from api.conf.base_config import BaseConfig
from api.conf.config import ConfigModel
from utils.common import singleton_with_lock

_TYPE_CHECKING = False


class CredentialsModel(BaseModel):
    revchatgpt_access_token: Optional[str] = None
    # chatgpt_account_username: Optional[str] = None
    # chatgpt_account_password: Optional[str] = None
    openai_api_key: Optional[str] = None


@singleton_with_lock
class Credentials(BaseConfig[ConfigModel]):
    if _TYPE_CHECKING:
        revchatgpt_access_token: Optional[str]
        # chatgpt_account_username: Optional[str]
        # chatgpt_account_password: Optional[str]
        openai_api_key: Optional[str]

    def __init__(self):
        super().__init__(CredentialsModel, "credentials.yaml")


if __name__ == '__main__':
    credentials = Credentials()
    credentials._model = CredentialsModel()
    credentials._config_path = './credentials.example.yaml'
    credentials.save()
