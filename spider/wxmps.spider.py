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
import json
import re
import time
from datetime import datetime

import requests
import urlparse
import pdfkit



class WxMps(object):
    """微信公众号文章、评论抓取爬虫"""
    def __init__(self, _biz, _pass_ticket, _app_msg_token, _cookie, _origin = '', _offset=0):
        self.origin = _origin
        self.offset = _offset
        self.biz = _biz  # 公众号标志
        self.msg_token = _app_msg_token  # 票据(非固定)
        self.pass_ticket = _pass_ticket  # 票据(非固定)
        self.headers = {
            'Cookie': _cookie,  # Cookie(非固定)
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat QBCore/3.43.27.400 QQBrowser/9.0.2524.400'
        }
        self.__db = dbmanager.DB(conf=config.DB)  # 数据库配置

    def start(self):
        """请求获取公众号的文章接口"""

        offset = self.offset
        while True:
            api = 'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&__biz={0}&f=json&offset={1}' \
                  '&count=10&is_ok=1&scene=124&uin=777&key=777&pass_ticket={2}&wxtoken=&appmsg_token' \
                  '={3}&x5=1&f=json'.format(self.biz, offset, self.pass_ticket, self.msg_token)

            resp = requests.get(api, headers=self.headers,verify=False).json()
            ret, status = resp.get('ret'), resp.get('errmsg')  # 状态信息
            if ret == 0 or status == 'ok':
                print('已获取文章列表，正在分析……')
                offset = resp['next_offset']  # 下一次请求偏移量
                general_msg_list = resp['general_msg_list']
                msg_list = json.loads(general_msg_list)['list']  # 获取文章列表
                for msg in msg_list:
                    comm_msg_info = msg['comm_msg_info']  # 该数据是本次推送多篇文章公共的
                    msg_id = comm_msg_info['id']  # 文章id
                    publish_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(comm_msg_info['datetime']))  # 发布时间
                    msg_type = comm_msg_info['type']  # 文章类型
                    # msg_data = json.dumps(comm_msg_info, ensure_ascii=False)  # msg原数据
                    if msg_type == 49:
                        #图文消息
                        app_msg_ext_info = msg.get('app_msg_ext_info')  # article原数据

                        if app_msg_ext_info:
                            # 本次推送的首条文章
                            self._parse_articles(app_msg_ext_info, msg_id, publish_time, msg_type, 1)
                            # 本次推送的其余文章
                            multi_app_msg_item_list = app_msg_ext_info.get('multi_app_msg_item_list')
                            if multi_app_msg_item_list:
                                for item in multi_app_msg_item_list:
                                    msg_id = item['fileid']  # 文章id
                                    if msg_id == 0:
                                        msg_id = int(time.time() * 1000)  # 设置唯一id,解决部分文章id=0出现唯一索引冲突的情况
                                    self._parse_articles(item, msg_id, publish_time, msg_type, 0)
                    elif msg_type == 1:
                        #文字消息
                        content = comm_msg_info.get('content')
                        #入库程序，待完善
                    elif msg_type == 3:
                        #图片消息
                        image_msg_ext_info = msg.get('image_msg_ext_info')
                        cdn_url = image_msg_ext_info.get('cdn_url')
                        #入库程序，待完善
                print('next offset is %d' % offset)
            else:
                print('微信验证错误 , Current offset is %d' % offset)
                break

    def _parse_articles(self, info, msg_id, publish_time, msg_type, is_main):
        """解析嵌套文章数据并保存入库"""

        title = info.get('title')  # 标题
        cover = info.get('cover')  # 封面图
        author = info.get('author')  # 作者
        digest = info.get('digest')  # 关键字
        source_url = info.get('source_url')  # 原文地址
        content_url = info.get('content_url')  # 微信地址
        is_multi = info.get('is_multi') if info.get('is_multi') else 0  # 是否多图文
        copyright_stat = '原创' if info.has_key('copyright_stat') and info['copyright_stat'] == 11 else '非原创'
        article_type = msg_type
        # ext_data = json.dumps(info, ensure_ascii=False)  # 原始数据

        content_url = content_url.replace('amp;', '').replace('#wechat_redirect', '').replace('http', 'https')



        # article保存入库
        info = {"title": title, "content_url": content_url, "cover": cover, "author": author,"is_multi": is_multi,
                "copyright_stat": copyright_stat,"source_url":source_url,"msg_id":msg_id,"is_main":is_main,
                "publish_time": publish_time, "origin": origin, "article_type": article_type, "digest": digest}
        r = self.__db.selectOne("mp_article", where="title = '%s' and publish_time = '%s'" % (title, publish_time))
        article_id = 0
        if not r:
            print digest
            self.__db.insert("mp_article", params_dic=info)
            article_id = self.__db.get_inserted_id()
        if article_id:
            # 文章详情保存入库
            contentInfo = self.crawl_article_content(content_url)
            print contentInfo
            print article_id
            contentInfo['article_id'] = article_id
            self.__db.insert("mp_content", params_dic=contentInfo)
            self._parse_article_detail(content_url, article_id)

    def crawl_article_content(self,content_url):
        """抓取文章内容、点赞数、评论数
        :param content_url: 文章地址
        """

        try:
            html = requests.get(content_url, verify=False).text
            # pdfkit.from_string(content_url, 'data/files/test.pdf')
        except:
            pass
        else:
            bs = BeautifulSoup(html, 'html.parser')
            content = ''
            js_content = bs.find(id='js_content')
            if js_content:
                p_list = js_content.find_all('p')
                content_list = list(map(lambda p: p.text, filter(lambda p: p.text != '', p_list)))
                content = ''.join(content_list)

            data = {"html": bs,"content": content}
            return data


    def _parse_article_detail(self, content_url, article_id=0):
        """从文章页提取相关参数用于获取评论,article_id是已保存的文章id"""

        try:
            body = requests.get(content_url, headers=self.headers, verify=False).text  # 文章详情
        except Exception as e:
            print('获取评论失败' + content_url)
        else:
            # group(0) is current line
            str_comment = re.search(r'var comment_id = "(.*)" \|\| "(.*)" \* 1;', body)
            str_msg = re.search(r"var appmsgid = '' \|\| '(.*)'\|\|", body)
            str_token = re.search(r'window.appmsg_token = "(.*)";', body)

            # 更新文章阅读数、评论数
            self._crawl_msgstat(content_url, article_id)
            # 抓取评论数据
            if str_comment and str_msg and str_token:
                comment_id = str_comment.group(1)  # 评论id(固定)
                app_msg_id = str_msg.group(1)  # 票据id(非固定)
                appmsg_token = str_token.group(1)  # 票据token(非固定)

                # 缺一不可
                if appmsg_token and app_msg_id and comment_id:
                    print('开始抓取评论……')
                    self._crawl_comments(app_msg_id, comment_id, appmsg_token, article_id)

    def _crawl_msgstat(self, content_url, article_id):
        """抓取文章的浏览数、点赞数、评论数,url及参数已确定，还需正则匹配mid、sn、idx参数即可"""
        data = {
            "is_only_read": "1",
            "is_temp_url": "0",
            "appmsg_type": "9",  # 新参数，不加入无法获取like_num
        }

        """
        添加请求参数
        __biz对应公众号的信息，唯一
        mid、sn、idx分别对应每篇文章的url的信息，需要从url中进行提取
        key、appmsg_token从fiddler上复制即可
        pass_ticket对应的文章的信息，貌似影响不大，也可以直接从fiddler复制
        """

        # 由于上面这种方法可能会获取数据失败，可以采取字符串拼接这种方法
        result = urlparse.urlparse(content_url)
        params = urlparse.parse_qs(result.query)

        print '正在抓取阅读数……'
        origin_url = "https://mp.weixin.qq.com/mp/getappmsgext?"
        appmsgext_url = origin_url + "__biz={}&mid={}&sn={}&idx={}&appmsg_token={}&x5=0&f=json".format(self.biz, params['mid'][0],
                                                                                                params['sn'][0], params['idx'][0],
                                                                                                self.msg_token)
        content = requests.post(appmsgext_url, headers=self.headers, data=data, verify=False).json()
        # 提取其中的阅读数和点赞数
        like_num = read_num = 0
        try:
            like_num = content["appmsgstat"]["like_num"] if content else 0
            read_num = content["appmsgstat"]["read_num"] if content else 0
            print "阅读数抓取成功"
        except:
            print "阅读数抓取失败"
        self.__db.update("mp_article", params_dic={"like_num": like_num,"read_num": read_num},where="article_id = %d" % article_id)
        time.sleep(round(1, 3))


    def _crawl_comments(self, app_msg_id, comment_id, appmsg_token, article_id):
        """抓取文章的评论"""

        api = 'https://mp.weixin.qq.com/mp/appmsg_comment?action=getcomment&scene=0&__biz={0}' \
              '&appmsgid={1}&idx=1&comment_id={2}&offset=0&limit=100&uin=777&key=777' \
              '&pass_ticket={3}&wxtoken=777&devicetype=android-26&clientversion=26060739' \
              '&appmsg_token={4}&x5=1&f=json'.format(self.biz, app_msg_id, comment_id,
                                                     self.pass_ticket, appmsg_token)

        resp = requests.get(api, headers=self.headers, verify=False).json()
        ret, status = resp['base_resp']['ret'], resp['base_resp']['errmsg']
        if ret == 0 or status == 'ok':
            elected_comment = resp['elected_comment']
            for comment in elected_comment:
                nick_name = comment.get('nick_name')  # 昵称
                logo_url = comment.get('logo_url')  # 头像
                comment_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(comment['create_time']))  # 评论时间
                content = comment.get('content')  # 评论内容
                content_id = comment.get('content_id')  # id
                like_num = comment.get('like_num')  # 点赞数
                is_top = comment.get('is_top')
                # reply_list = comment.get('reply')['reply_list']  # 回复数据
                info = {"article_id":article_id,"comment_id":comment_id,"nick_name":nick_name,"logo_url":logo_url,"content_id":content_id,"content":content,"is_top":is_top,
                        "like_num": like_num,"comment_time":comment_time,"create_time":time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))}

                self.__db.insert("mp_comment", info)
            print "评论抓取完成"


if __name__ == '__main__':
    biz = 'MjM5Mzg3OTg4MQ=='  # "Python爱好者社区"
    pass_ticket = 'mCDqEQb9JT3AYKqw/6hakCFM9eUo qol Uv S6ORg7ql7n4/5Ozq4H3CnKLBn3g/'
    app_msg_token = '1005_YE8yJ1udn%2F9jnfwheYO1ke0WJZeNgbnGqjl1bg~~'
    cookie = 'wxuin=1981385113; devicetype=Windows10; version=62060739; lang=zh_CN; pass_ticket=mCDqEQb9JT3AYKqw/6hakCFM9eUo+qol+Uv+S6ORg7ql7n4/5Ozq4H3CnKLBn3g/; wap_sid2=CJmT5rAHElxiMXNnTHdFaVNOS2ctWElfT1BxQVZLcjRRZ2ZxT004SUR1WENHWk5scDdleXVKQWl6U1ZIY0d3QjUtdjU0NGt4WjVwR1ZlZVZXSWEyak9MSWpwMEt6LTBEQUFBfjCD6ODlBTgNQJVO'

    origin = 'Python爱好者社区'
    # 以上信息不同公众号每次抓取都需要借助抓包工具做修改
    wxMps = WxMps(biz, pass_ticket, app_msg_token, cookie, origin, 0)
    wxMps.start()  # 开始爬取文章及评论

