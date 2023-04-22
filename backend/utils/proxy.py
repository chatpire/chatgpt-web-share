import os, subprocess
from api.conf import Config
import api.globals as g

from utils.logger import get_logger

logger = get_logger(__name__)
_config = Config().get_config()


def run_reverse_proxy():
    """暂时不再使用"""
    return

    if not _config.chatgpt.is_plus_account:
        logger.error("You need a ChatGPT Plus account to use the reverse proxy!")
        logger.error("Please set chatgpt_paid to true in config.yaml and restart the server.")
        exit(1)

    proxy_path = _config.reverse_proxy.binary_path
    if not proxy_path:
        logger.error("You need to set the reverse proxy binary path in config.yaml!")
        exit(1)

    puid = _config.reverse_proxy.puid
    env_vars = {"PORT": str(_config.reverse_proxy.port)}
    http_proxy = _config.reverse_proxy.http_proxy
    if puid:
        env_vars["PUID"] = puid
    if _config.reverse_proxy.auto_refresh_puid:
        env_vars["ACCESS_TOKEN"] = _config.credentials.chatgpt_account_token
    if http_proxy:
        env_vars["http_proxy"] = http_proxy
        logger.info(f"Reverse proxy Using http proxy: {http_proxy}")
    g.reverse_proxy_log_file = open(os.path.join(_config.log.log_dir, "logs"), "reverse_proxy.log", "w",
                                    encoding="utf-8")
    logger.debug(f"Reverse proxy binary path: {proxy_path}")
    g.reverse_proxy_process = subprocess.Popen([proxy_path], env=env_vars, stdout=g.reverse_proxy_log_file,
                                               stderr=g.reverse_proxy_log_file)
    logger.info("Reverse proxy started!")


def close_reverse_proxy():
    return

    if g.reverse_proxy_process:
        g.reverse_proxy_process.kill()
        g.reverse_proxy_process = None
        g.reverse_proxy_log_file.close()
        g.reverse_proxy_log_file = None
        logger.info("Reverse proxy stopped.")
