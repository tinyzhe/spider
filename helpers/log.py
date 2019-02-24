# -*- coding:utf-8 -*-
__author__ = 'xiangzhe'

import logging
import datetime
from conf import config

log_format = '[%(asctime)s] %(filename)s [%(levelname)s] %(message)s'
filename = config.FILE_LOG_DIR + '/' + datetime.datetime.now().strftime('%Y%m%d') + '.log'
#filename = datetime.datetime.now().strftime('%Y%m%d') + '.log'

logging.basicConfig(format=log_format,datefmt='%Y-%m-%d %H:%M:%S %p',level=logging.DEBUG, filename=filename, filemode='a')

# 定义一个Handler打印INFO及以上级别的日志到sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter('[%(asctime)s] %(filename)s [%(levelname)s] %(message)s'))
logging.getLogger().addHandler(console)

logger = logging.getLogger()