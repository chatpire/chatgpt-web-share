import os
import shutil

from typing import TypeVar, Generic, Type, get_args

from pydantic import BaseModel
from ruamel.yaml import YAML
from fastapi.encoders import jsonable_encoder

from api.exceptions import ConfigException

T = TypeVar("T", bound=BaseModel)


class BaseConfig(Generic[T]):
    _model: T = None
    _config_path = None
    _model_type = None

    def __init__(self, model_type: Type[BaseModel], config_filename: str, load_config: bool = True):
        self._model_type = model_type
        config_dir = os.environ.get('CWS_CONFIG_DIR', './data/config')
        self._config_path = os.path.join(config_dir, config_filename)
        if load_config:
            self.load()
        else:
            self._model = self._model_type()

    def __getattr__(self, key):
        return getattr(self._model, key)

    def __setattr__(self, key, value):
        if key in ('_model', '_config_path', '_model_type'):
            super().__setattr__(key, value)
        else:
            setattr(self._model, key, value)

    def schema(self):
        return self._model.schema()

    def model(self):
        return self._model.copy()

    def update(self, model: T):
        self._model = self._model_type.model_validate(model)

    def load(self):
        if not os.path.exists(self._config_path):
            raise ConfigException(f"Config file not found: {self._config_path}")
        try:
            with open(self._config_path, mode='r', encoding='utf-8') as f:
                # 读取配置
                yaml = YAML()
                config_dict = yaml.load(f) or {}
                self._model = self._model_type.model_validate(config_dict)
        except Exception as e:
            raise ConfigException(f"Cannot read config ({self._config_path}), error: {str(e)}")

    def save(self):
        config_dict = jsonable_encoder(self._model.model_dump())
        # 复制 self._config_path 备份一份
        config_dir = os.path.dirname(self._config_path)
        if not os.path.exists(config_dir):
            raise ConfigException(f"Config dir not found: {config_dir}")
        backup_config_path = os.path.join(config_dir, f"{os.path.basename(self._config_path)}.backup.yaml")
        shutil.copyfile(self._config_path, backup_config_path)
        with open(self._config_path, mode='w', encoding='utf-8') as sf:
            yaml = YAML()
            yaml.dump(config_dict, sf)
