"""
modified from NAStool/nas-tools/config.py
"""

import os
from threading import Lock
from ruamel.yaml import YAML
from api.conf.config_model import ConfigModel

# 线程锁
lock = Lock()

# 全局实例
_CONFIG = None


def singleConfig(cls):
    def _singleConfig(*args, **kwargs):
        global _CONFIG
        if not _CONFIG:
            with lock:
                _CONFIG = cls(*args, **kwargs)
        return _CONFIG

    return _singleConfig


@singleConfig
class Config(object):
    _config_path = None
    _config_dict = None
    _config: ConfigModel = None

    def __init__(self):
        self._config_path = os.environ.get('CWS_CONFIG_PATH', './config.yaml')
        if not os.environ.get('TZ'):
            os.environ['TZ'] = 'Asia/Shanghai'

        if not os.path.exists(self._config_path):
            print("Error: Config file not found: %s" % self._config_path)
            quit(1)

        try:
            with open(self._config_path, mode='r', encoding='utf-8') as f:
                # 读取配置
                yaml = YAML()
                self._config_dict = yaml.load(f) or {}
        except Exception as e:
            print(f"Error: Cannot read config ({self._config_path}), file format error: {str(e)}")
            quit(1)

        self._config = ConfigModel(**self._config_dict)

    def get_config(self) -> ConfigModel:
        return self._config

    def save_config(self, new_cfg: ConfigModel):
        self._config = new_cfg
        self._config_dict = new_cfg.dict()
        with open(self._config_path, mode='w', encoding='utf-8') as sf:
            yaml = YAML()
            yaml.dump(self._config_dict, sf)

    def get_config_path(self):
        return os.path.dirname(self._config_path)


if __name__ == '__main__':
    # 用于生成默认配置文件
    cfg = Config()
    cfg._config_path = './config.example.yaml'
    cm = ConfigModel()
    cfg.save_config(cm)
