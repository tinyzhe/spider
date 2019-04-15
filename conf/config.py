# -*- coding:utf-8 -*-
__author__ = 'xiangzhe'

import os
import sys

'''
系统配置文件
'''

SYSTEM_ROOT = os.path.split(os.path.realpath(sys.argv[0]))[0]

FILE_SAVE_DIR = SYSTEM_ROOT + '/' + 'data'
FILE_TEMP_DIR = SYSTEM_ROOT + '/' + 'data/temp'
FILE_LOG_DIR = SYSTEM_ROOT + '/' + 'data/log'


DB = {
    'host':'127.0.0.1',
    'user':'root',
    'password':'root',
    'port':3306,
    'dbname':'spider'
}

