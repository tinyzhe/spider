#coding=utf-8
__author__ = 'xiangzhe'

def getCoding(strInput):
    '''
    获取编码格式
    '''
    if isinstance(strInput, unicode):
        return "unicode"

    try:
        strInput.decode("utf-8")
        return 'utf-8'
    except Exception as e:
        pass

    try:
        strInput.decode("gbk")
        return 'gbk'
    except Exception as e:
        pass

def str2UNICODE(strInput):
    '''
    转化为unicode格式
    '''
    strCodingFmt = getCoding(strInput)
    if strCodingFmt == "utf-8":
        unicode(strInput,"utf-8")
    elif strCodingFmt == "unicode":
        pass
    elif strCodingFmt == "gbk":
        strInput = unicode(strInput,"gbk")
    return strInput

def str2UTF8(strInput):
    '''
    转化为utf8格式
    '''
    strCodingFmt = getCoding(strInput)
    if strCodingFmt == "utf-8":
        pass
    elif strCodingFmt == "unicode":
        strInput.encode("utf-8")
    elif strCodingFmt == "gbk":
        strInput = unicode(strInput,"gbk").encode("utf-8")
    return strInput

def str2GBK(strInput):
    '''
    转化为gbk格式
    '''
    strCodingFmt = getCoding(strInput)
    if strCodingFmt == "gbk":
        return strInput
    elif strCodingFmt == "unicode":
        return strInput.encode("gbk")
    elif strCodingFmt == "utf8":
        return strInput.decode("utf8").encode("gbk")