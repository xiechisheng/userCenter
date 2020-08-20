import datetime
import json
from django.core import signing
from django.conf import settings
from django.core.cache import cache, caches
from rest_framework.response import Response


import logging as logObj
logger = logObj.getLogger("uc")


def tokenEncode(objDict):
    """
    Token信息--编码
    """
    try:
        tokenValue = signing.dumps(objDict, settings.SECRET_KEY)
        cache.set(objDict["login"], tokenValue, settings.TOKEN_TIME_OUT)
    except Exception as err:
        print("Token Create Error Message: " + format(err))
        return None
    else:
        return tokenValue


def tokenDecode(objToken):
    """
    Token信息--解码
    """
    try:
        src = signing.loads(objToken, settings.SECRET_KEY)
    except Exception as err:
        return None
    else:
        return src


def tokenQuery(login):
    """
    Token信息--查询
    """
    try:
        tokenValue = cache.get(login)
    except Exception as err:
        return None
    else:
        return tokenValue


def tokenDelete(login):
    """
    Token信息--删除
    """
    try:
        tokenValue = cache.get(login)
    except Exception as err:
        return False
    else:
        if tokenValue is None:
            return True
        else:
            cache.delete(login)
            return True


def addErrLogByErrObj(path=None, login=None, client=None, errMsg=None, errObj=None):
    logMsg = ""
    if path is not None:
        logMsg += "[" + path + "]"
    if login is not None:
        logMsg += "[" + login + "]"
    if client is not None:
        logMsg += "[" + client + "]"
    if errMsg is not None:
        if errObj is None:
            logMsg += "[" + errMsg + "]"
        else:
            logMsg += "[" + errMsg + "<" + format(errObj) + ">" + "]"

    if logMsg is not None:
        logger.error(logMsg)


def addHttpResponeLog(path=None, login=None, client=None, requestData=None, responeData=None):
    logMsg = ""
    if path is not None:
        logMsg += "[" + path + "]"
    if login is not None:
        logMsg += "[" + login + "]"
    if client is not None:
        logMsg += "[" + client + "]"
    if requestData is not None:
        logMsg += "[" + format(requestData) + "]"
    if requestData is not None:
        logMsg += "[" + format(responeData) + "]"

    if logMsg:
        if responeData["result"] == 0:
            logger.info(logMsg)
        else:
            logger.error(logMsg)


def postHttpResponse(requestData, responseData, httpCode = 200):
    try:
        path = None
        login = None
        client = None
        postBody = None

        if "path" in requestData:
            path = requestData["path"]
        if ("user_info" in requestData) and ("login" in requestData["user_info"]):
            login = requestData["user_info"]["login"]
        if "client" in requestData:
            client = requestData["client"]
        if "post_body" in requestData:
            postBody = requestData["post_body"]

        addHttpResponeLog(path, login, client, postBody, responseData)
    except Exception as err:
        print("Http Response Error Message: " + format(err))
        pass

    return Response(responseData, status=httpCode, content_type="application/json")


def postRequestParser(request):
    requestData = {}
    try:
        requestData["success"] = 0
        requestData["client"] = request.META["REMOTE_ADDR"]
        requestData["path"] = request.path
    except Exception as err:
        addErrLogByErrObj(requestData["path"], None, requestData["client"], "Header信息获取失败", err)
        return requestData
    requestData["success"] = 1

    loginToken = None
    try:
        loginToken = request.META.get("HTTP_AUTHENTICATION")
    except KeyError:
        addErrLogByErrObj(requestData["path"], None, requestData["client"], "Token信息获取失败<KeyError>", None)

    tokenData = None
    try:
        if loginToken:
            tokenData = tokenDecode(loginToken)
            tokenCache = tokenQuery(tokenData["login"])
            if tokenData and tokenCache and (tokenCache == loginToken):
                requestData["user_info"] = tokenData
    except Exception as err:
        addErrLogByErrObj(requestData["path"], None, requestData["client"], "Token信息解析失败1", err)

    reqBody = None
    try:
        reqBody = json.loads(request.body)
    except Exception as err:
        requestData["post_body"] = {}
        addErrLogByErrObj(requestData["path"], tokenData["login"], requestData["client"], "Post信息解析失败2", err)
    else:
        requestData["post_body"] = reqBody

    return requestData


def addDebugOrTestLog(logMsg):
    if settings.DEBUG:
        logger.debug(logMsg)

