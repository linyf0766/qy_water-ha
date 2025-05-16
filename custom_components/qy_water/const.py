"""Constants for qy_water integration."""
from datetime import timedelta
import logging

DOMAIN = "qy_water"
LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL = 10  # 默认更新间隔10分钟
CONF_OID = "oid"
CONF_UPDATE_TIME = "updatetime"

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; 23013R Build/TKQ1.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.1 Mobile Safari/537.36 XWEB/1260213 MMWEBSDK/202305 /2731 MicroMessenger/8.0.42.2460(0x28002A58) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64"
BASE_URL = "https://wechat.qygs3388000.com/wx_main.php?mid=VCX_1_2"

# 调试模式
DEBUG = True
if DEBUG:
    LOGGER.setLevel(logging.DEBUG)
    logging.getLogger('urllib3').setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.ERROR)