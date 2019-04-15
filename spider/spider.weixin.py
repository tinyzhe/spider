# -*- coding:utf-8 -*-
__author__ = 'xiangzhe'

#coding=utf-8

"""
采集微信公众号历史数据
"""

import time
import requests
import json
import datetime
from bs4 import BeautifulSoup
import os
import sys
import re
from conf import config
from libs import dbmanager
from helpers import log

reload(sys)
sys.setdefaultencoding('utf-8')

class Processor():

    def __init__(self):
        self.__db = dbmanager.DB(conf=config.DB)

    def run(self):
        self.spider()

        """
        "list": [ //最外层的键名；只出现一次，所有内容都被它包含。
            {//这个大阔号之内是一条多图文或单图文消息，通俗的说就是一天的群发都在这里
            "app_msg_ext_info":{//图文消息的扩展信息
            "content_url": "图文消息的链接地址",
            "cover": "封面图片",
            "digest": "摘要",
            "is_multi": "是否多图文，值为1和0",
            "multi_app_msg_item_list": [//这里面包含的是从第二条开始的图文消息，如果is_multi=0，这里将为空
            {
            "content_url": "图文消息的链接地址",
            "cover": "封面图片",
            "digest": ""摘要"",
            "source_url": "阅读原文的地址",
            "title": "子内容标题"
            },
            ...//循环被省略
            ],
            "source_url": "阅读原文的地址",
            "title": "头条标题"
            },
            "comm_msg_info":{//图文消息的基本信息
            "datetime": '发布时间，值为unix时间戳',
            "type": 49 //类型为49的时候是图文消息
            }
            },
            ...//循环被省略
            ]
            
            点赞阅读量接口研究：https://blog.csdn.net/qq_19383667/article/details/79380212
        """
    def spider(self):

        requestHeaders = {
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate, compress',
            # 'Accept-Language': 'zh-CN,zh;q=0.8',
            # 'Cache-Control': 'max-age=0',
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0'
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat QBCore/3.43.1021.400 QQBrowser/9.0.2524.400',
        }

        requestHeaders['Cookie'] = 'rewardsn=; wxtokenkey=777; wxuin=1981385113; devicetype=Windows10; version=62060739; lang=zh_CN; pass_ticket=LIFYpBO1DldToCdN7Lk7rsEnTZZRprDfnRKofMV3WU+PI/cgHsDkbjvC/+e/eZQM; wap_sid2=CJmT5rAHElw0ZGl6X3JjNHpYclF5UTdNbi1UODRPWGRUbVJaY2FGYl9DUzdJVHFMel96OE40bGVDVmR1bDRxeU1ndXNXOGRZWWFnTzZnWXJZM1BjaGJqd2JreWFvZXdEQUFBfjC9hNHlBTgNQJVO'

        host_url = "https://mp.weixin.qq.com"
        target_url = "/mp/profile_ext?action=getmsg&__biz=MzIwOTA3Njg3MQ==&f=json&offset=10&count=10&is_ok=1&scene=124&uin=MTk4MTM4NTExMw%3D%3D&key=7c2de03dd17390139ef9f69a48ee3d8cdc58b21bb9385d6fce65767425302437c2694dee53b204753bcea8fb585ec632bf759d118662695b0bd5659d57044635d3ecb053be69d3b406b6a5b529c2d9d4&pass_ticket=LIFYpBO1DldToCdN7Lk7rsEnTZZRprDfnRKofMV3WU%2BPI%2FcgHsDkbjvC%2F%2Be%2FeZQM&wxtoken=&appmsg_token=1004_82TgTROciyuhltJERpY9hJfKhAgrJszMcvrC4Q~~&x5=0&f=json HTTP/1.1"

        page = 49
        pagesize = 10
        while True:
            url = host_url + target_url
            start = str((page-1) * pagesize)
            url = url.replace("&offset=10","&offset=" + start)

            headers = requestHeaders

            # 导入数据
            try:
                resCode = requests.get(url, headers=headers, timeout=20,verify=False)
            except Exception as e:
                log.logger.exception(e)
                time.sleep(10)
                resCode = requests.get(url, headers=headers, timeout=20,verify=False)
            res =  json.loads(resCode.text)
            general_msg_list = json.loads(res['general_msg_list'])
            list = general_msg_list['list']
            for value in list:
                comm_msg_info = value['comm_msg_info']
                datetime = comm_msg_info['datetime'] # 时间戳
                datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(datetime))
                article_type = comm_msg_info['type']
                if article_type == 49:
                    article_type = '图文消息'
                    app_msg_ext_info = value['app_msg_ext_info']
                    title = app_msg_ext_info['title'] #标题
                    cotent_url = app_msg_ext_info['content_url'].replace("&amp;","&") #内容url
                    cover = app_msg_ext_info['cover'] #封面
                    author = app_msg_ext_info['author'] #作者
                    copyright_stat = '原创' if app_msg_ext_info.has_key('copyright_stat') and app_msg_ext_info['copyright_stat'] == 11 else '非原创'
                    print '%s--%s--%s--%s' % (title,author,copyright_stat,datetime)
                    # 抓取文章内容
                    # contentCode = requests.get(cotent_url, headers=headers, timeout=20,verify=False)
                    # contentCode.encoding = 'utf-8'
                    # bsCode = BeautifulSoup(contentCode.text, "lxml")

                    info = {"title":title,"cotent_url":cotent_url,"cover":cover,"author":author,"copyright_stat":copyright_stat,"publish_time":datetime,"origin":"行测风暴羚羊","article_type":article_type}
                    r = self.__db.selectOne("weixin_spider",where="title = '%s' and publish_time = '%s'" % (title,datetime))
                    if not r:
                        self.__db.insert("weixin_spider",params_dic=info)

            page += 1

Processor().run()