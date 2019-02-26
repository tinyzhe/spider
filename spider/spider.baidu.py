# -*- coding:utf-8 -*-
__author__ = 'xiangzhe'

#coding=utf-8

"""
采集百度搜索首页内容到数据库
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
    #百度搜索url
    url = "https://baidu.com"
    #模拟浏览器请求头
    requestHeaders = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, compress',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0'
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    }

    exceptionAreaIds = []

    def __init__(self):
        self.__db = dbmanager.DB(conf=config.DB)

    def run(self):
        self.spider()

    def spider(self):
        areas = self.__db.selectAll('god_area',columns="cid,slug,category_name",where="status = 1 and level < 3 order by cid asc,level asc")
        for area in areas:
            searchKey = str(area['category_name']) + '林长制'
            url  = self.url + "/s?wd=" + searchKey
            resCode = requests.get(url, headers=self.requestHeaders, timeout=20)
            resCode.encoding = 'utf-8'
            bsCode = BeautifulSoup(resCode.text, "lxml")

            self.formatInfo(bsCode=bsCode,area=area,searchKey=searchKey)

            pageDiv = bsCode.find("div",id="page")
            pageList = pageDiv.find_all("a")
            pageInfo = {}
            for p in pageList:
                pageUrl = p.get("href")
                pageUrl = self.url + str(pageUrl)
                page = p.get_text()
                if page != '下一页':
                    pageInfo[page] = pageUrl
                    print '--page is %s--' % page
                    print '--pageUrl is %s--' % pageUrl
                    pageResCode = requests.get(pageUrl, headers=self.requestHeaders, timeout=20)
                    pageResCode.encoding = 'utf-8'
                    pageBsCode = BeautifulSoup(resCode.text, "lxml")
                    self.formatInfo(bsCode=pageBsCode, area=area, searchKey=searchKey)
            time.sleep(10)


    def get_real(self, o_url):
        '''获取重定向url指向的网址'''
        r = requests.get(o_url, allow_redirects=False)  # 禁止自动跳转
        if r.status_code == 302:
            try:
                return r.headers['location']  # 返回指向的地址
            except:
                pass
        return o_url  # 返回源地址

    def formatInfo(self,bsCode,area,searchKey):
        content = bsCode.select('#content_left')
        list = bsCode.find_all("div", class_="result")
        for info in list:
            title = str(info.find("a").get_text())
            href = info.find("a").get("href")
            abstract = str(info.find("div", class_="c-abstract").get_text())
            try:
                realUrl = self.get_real(href)
            except Exception as e:
                log.logger.info(e)
                self.exceptionAreaIds.append(area['cid'])
                log.logger.info(','.join(self.exceptionAreaIds))

            keywords = ['会议', '评审', '试行', '考察', '启动', '推行', '规划','改革']
            for key in keywords:
                if title.find(key) != -1 or abstract.find(key) != -1:
                    sourceInfo = self.__db.selectOne('god_baidu_spider_page', where="resource_url = '%s'" % realUrl)
                    if not sourceInfo:
                        params = {"title": title, "abstract": abstract, "search_key": searchKey, "area_id": area['cid'],
                                  "resource_url": realUrl}
                        self.__db.insert('god_baidu_spider_page', params_dic=params)
                        print title
                        break


Processor().run()