import os
from typing import TypeVar, Generic, Type
from pydantic import BaseModel
from ruamel.yaml import YAML

from api.exceptions import ConfigException

T = TypeVar("T", bound=BaseModel)


class BaseConfig(Generic[T]):
    _model: T = None
    _config_path = None
    _model_type = None

    def __init__(self, model_type: Type, config_filename: str):
        self._model_type = model_type
        config_dir = os.environ.get('CWS_CONFIG_DIR', './config')
        self._config_path = os.path.join(config_dir, config_filename)

    def __getattr__(self, key):
        return getattr(self._model, key)

    def __setattr__(self, key, value):
        if key in ('_model', '_config_path', '_model_type'):
            super().__setattr__(key, value)
        else:
            setattr(self._model, key, value)

    def load(self):
        if not os.path.exists(self._config_path):
            raise ConfigException(f"Config file not found: {self._config_path}")
        try:
            with open(self._config_path, mode='r', encoding='utf-8') as f:
                # 读取配置
                yaml = YAML()
                config_dict = yaml.load(f) or {}
                self._model = self._model_type(**config_dict)
        except Exception as e:
            raise ConfigException(f"Cannot read config ({self._config_path}), error: {str(e)}")

    def save(self):
        config_dict = self._model.dict()
        with open(self._config_path, mode='w', encoding='utf-8') as sf:
            yaml = YAML()
            yaml.dump(config_dict, sf)
