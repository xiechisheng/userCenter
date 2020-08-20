import datetime
from django.db import transaction
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password

from api.public import postRequestParser, postHttpResponse
from api.public import tokenEncode, tokenDelete
from api.errorCode import getErrMsgByCode
from api.models import user as userDB

def getUserInfoByID(userID):
    """
    根据用户ID返回用户的基本信息
    """
    userInfo = {}
    try:
        userObj = userDB.objects.get(id=userID)
        userInfo["id"] = userObj.id
        userInfo["login"] = userObj.login
        userInfo["name"] = userObj.nickname
        userInfo["role"] = userObj.role
        userInfo["enable"] = userObj.enable
        userInfo["deleted"] = userObj.deleted
        userInfo["register"] = userObj.register
    except Exception as err:
        return None

    return userInfo


@csrf_exempt
@api_view(["post"])
def userLogin(request):
    """
    用户信息--登录
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10000001, "msg": getErrMsgByCode(10000001, None)}
        return postHttpResponse(requestData, responseData)

    reqBody = requestData["post_body"]
    if "login" not in reqBody:
        responseData = {"result": 10000002, "msg": getErrMsgByCode(10000002, None)}
        return postHttpResponse(requestData, responseData)
    else:
        loginName = reqBody["login"]
    if "password" not in reqBody:
        responseData = {"result": 10000003, "msg": getErrMsgByCode(10000003, None)}
        return postHttpResponse(requestData, responseData)
    else:
        loginPwd = reqBody["password"]

    userObj =None
    try:
        userObj = userDB.objects.get(login=loginName, deleted=0)
    except userDB.DoesNotExist:
        responseData = {"result": 10000004, "msg": getErrMsgByCode(10000004, None)}
        return postHttpResponse(requestData, responseData)

    if not check_password(loginPwd, userObj.password):
        responseData = {"result": 10000005, "msg": getErrMsgByCode(10000005, None)}
        return postHttpResponse(requestData, responseData)
    if userObj.enable == 0:
        responseData = {"result": 10000006, "msg": getErrMsgByCode(10000006, None)}
        return postHttpResponse(requestData, responseData)

    strTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tokenValue = tokenEncode({"id": userObj.id, "login": userObj.login, "role": userObj.role, "time": strTime})
    if tokenValue is None:
        responseData = {"result": 10000007, "msg": getErrMsgByCode(10000007, None)}
        return postHttpResponse(requestData, responseData)

    resData = {}
    resData["id"] = userObj.id
    resData["login"] = userObj.login
    resData["nickname"] = userObj.nickname
    resData["role"] = userObj.role
    resData["enable"] = userObj.enable
    resData["register"] = userObj.register
    resData["token"] = tokenValue

    responseData = {"result": 0, "msg": "OK", "data": resData}
    return postHttpResponse(requestData, responseData)


@csrf_exempt
@api_view(["post"])
def userLogout(request):
    """
    用户信息--登出
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10001001, "msg": getErrMsgByCode(10001001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10001002, "msg": getErrMsgByCode(10001002, None)}
        return postHttpResponse(requestData, responseData)

    tokenInfo = requestData["user_info"]
    if tokenDelete(tokenInfo["login"]) is False:
        responseData = {"result": 10001003, "msg": getErrMsgByCode(10001003, None)}
        return postHttpResponse(requestData, responseData)

    responseData = {"result": 0, "msg": "OK"}
    return postHttpResponse(requestData, responseData)


@csrf_exempt
@api_view(["post"])
def userInfoAdd(request):
    """
    用户信息--新增
    role: 9普通用户, 10管理员，11超级管理员
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10002001, "msg": getErrMsgByCode(10002001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10002002, "msg": getErrMsgByCode(10002002, None)}
        return postHttpResponse(requestData, responseData)

    userLoginedInfo = requestData["user_info"]

    userLogin = None
    userPassword = None
    userNickName = None
    userRole = None
    reqBody = requestData["post_body"]
    if "login" not in reqBody:
        responseData = {"result": 10002003, "msg": getErrMsgByCode(10002003, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userLogin = reqBody["login"]
    if "password" not in reqBody:
        responseData = {"result": 10002004, "msg": getErrMsgByCode(10002004, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userPassword = make_password(reqBody["password"], "mds")
    if "nickname" not in reqBody:
        responseData = {"result": 10002005, "msg": getErrMsgByCode(10002005, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userNickName = reqBody["nickname"]
    if "role" not in reqBody:
        responseData = {"result": 10002006, "msg": getErrMsgByCode(10002006, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userRole = reqBody["role"]

    if userDB.objects.filter(login=userLogin):
        responseData = {"result": 10002007, "msg": getErrMsgByCode(10002007, None)}
        return postHttpResponse(requestData, responseData)

    if userRole == 11:
        if userLoginedInfo["role"] < 11:
            return postHttpResponse(requestData, {"result": 10002008, "msg": getErrMsgByCode(10002008, None)})
    elif userRole == 10:
        if userLoginedInfo["role"] < 10:
            return postHttpResponse(requestData, {"result": 10002008, "msg": getErrMsgByCode(10002008, None)})
    elif userRole == 9:
        if userLoginedInfo["role"] < 10:
            return postHttpResponse(requestData, {"result": 10002008, "msg": getErrMsgByCode(10002008, None)})
    else:
        pass

    savePoint = transaction.savepoint()
    try:
        userObj = userDB()
        userObj.login = userLogin
        userObj.password = userPassword
        userObj.nickname = userNickName
        userObj.role = userRole
        userObj.save()
    except Exception as err:
        transaction.savepoint_rollback(savePoint)
        responseData = {"result": 10002009, "msg": getErrMsgByCode(10002009, err)}
        return postHttpResponse(requestData, responseData)

    transaction.savepoint_commit(savePoint)

    responseData = {"result": 0, "msg": "OK"}
    return postHttpResponse(requestData, responseData)


@csrf_exempt
@api_view(["post"])
def userInfoModify(request):
    """
    用户信息--修改
    role: 9普通用户, 10管理员，11超级管理员
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10003001, "msg": getErrMsgByCode(10003001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10003002, "msg": getErrMsgByCode(10003002, None)}
        return postHttpResponse(requestData, responseData)

    userID = None
    reqBody = requestData["post_body"]
    if "id" not in reqBody:
        responseData = {"result": 10003003, "msg": getErrMsgByCode(10003003, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userID = reqBody["id"]

    userLoginedInfo = requestData["user_info"]
    userObj = None
    try:
        userObj = userDB.objects.get(id=userID, deleted=0)
    except userDB.DoesNotExist:
        responseData = {"result": 10003004, "msg": getErrMsgByCode(10003004, None)}
        return postHttpResponse(requestData, responseData)

    if (userLoginedInfo["role"] < 10) and (userLoginedInfo["id"] != userID):
        print("User Logined Role:" + userLoginedInfo["login"] + " => " + str(userLoginedInfo["role"]))
        responseData = {"result": 10003005, "msg": getErrMsgByCode(10003005, None)}
        return postHttpResponse(requestData, responseData)

    userPassword = None
    userNickName = None
    userRole = None
    userEnable = None
    if "password" in reqBody:
        userPassword = reqBody["password"]
    if "nickname" in reqBody:
        userNickName = reqBody["nickname"]
    if "role" in reqBody:
        userRole = reqBody["role"]
    if "enable" in reqBody:
        userEnable = reqBody["enable"]
    if userLoginedInfo["role"] <=userObj.role:
        responseData = {"result": 10003006, "msg": getErrMsgByCode(10003006, None)}
        return postHttpResponse(requestData, responseData)

    with transaction.atomic():
        savePoint = transaction.savepoint()
        try:
            if userPassword:
                userObj.password = make_password(userPassword, "mds")
            if userNickName:
                userObj.nickname = userNickName
            if userRole:
                userObj.role = userRole
            if userEnable:
                userObj.enable = userEnable

            userObj.save()
        except Exception as err:
            transaction.savepoint_rollback(savePoint)
            responseData = {"result": 10003007, "msg": getErrMsgByCode(10003007, err)}
            return postHttpResponse(requestData, responseData)
        transaction.savepoint_commit(savePoint)

    responseData = {"result": 0, "msg": "OK"}
    return postHttpResponse(requestData, responseData)


@csrf_exempt
@api_view(["post"])
def userInfoQuery(request):
    """
    用户信息--查询
    role: 9普通用户, 10管理员，11超级管理员
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10004001, "msg": getErrMsgByCode(10004001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10004002, "msg": getErrMsgByCode(10004002, None)}
        return postHttpResponse(requestData, responseData)

    userID = None
    userLogin = None
    reqBody = requestData["post_body"]
    if "id" in reqBody:
        userID = reqBody["id"]
    if "login" in reqBody:
        userLogin = reqBody["login"]

    if (userID is None) and (userLogin is None):
        responseData = {"result": 10004003, "msg": getErrMsgByCode(10004003, None)}
        return postHttpResponse(requestData, responseData)

    userObj = None
    try:
        if userID:
            userObj = userDB.objects.get(id=userID, deleted=0)
        else:
            userObj = userDB.objects.get(login=userLogin, deleted=0)
    except userDB.DoesNotExist:
        responseData = {"result": 10004004, "msg": getErrMsgByCode(10004004, None)}
        return postHttpResponse(requestData, responseData)
    except Exception as err:
        responseData = {"result": 10004005, "msg": getErrMsgByCode(10004005, err)}
        return postHttpResponse(requestData, responseData)

    userLoginedInfo = requestData["user_info"]
    resData = {}
    resData["id"] = userObj.id
    resData["login"] = userObj.login
    resData["nickname"] = userObj.nickname
    resData["role"] = userObj.role
    resData["enable"] = userObj.enable
    resData["register"] = userObj.register

    responseData = {"result": 0, "msg": "OK", "data": resData}
    return postHttpResponse(requestData, responseData)


@csrf_exempt
@api_view(["post"])
def userInfoDelete(request):
    """
    用户信息--删除
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10005001, "msg": getErrMsgByCode(10005001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10005002, "msg": getErrMsgByCode(10005002, None)}
        return postHttpResponse(requestData, responseData)

    userID = None
    reqBody = requestData["post_body"]
    if "id" not in reqBody:
        responseData = {"result": 10005003, "msg": getErrMsgByCode(10005003, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userID = reqBody["id"]

    userObj = None
    try:
        userObj = userDB.objects.get(id=userID, deleted=0)
    except userDB.DoesNotExist:
        responseData = {"result": 10005004, "msg": getErrMsgByCode(10005004, None)}
        return postHttpResponse(requestData, responseData)

    userLoginedInfo = requestData["user_info"]
    if (userLoginedInfo["role"] < 10) or (userLoginedInfo["role"] <= userObj.role):
        responseData = {"result": 10005005, "msg": getErrMsgByCode(10005005, None)}
        return postHttpResponse(requestData, responseData)


    savePoint = transaction.savepoint()
    try:
        userObj.deleted = 1
        userObj.save()
    except Exception as err:
        transaction.savepoint_rollback(savePoint)
        responseData = {"result": 10005006, "msg": getErrMsgByCode(10005006, err)}
        return postHttpResponse(requestData, responseData)
    transaction.savepoint_commit(savePoint)

    responseData = {"result": 0, "msg": "OK"}
    return postHttpResponse(requestData, responseData)


@csrf_exempt
@api_view(["post"])
def userAccountRegistered(request):
    """
    用户信息--是否注册
    registered: 0未注册, 1已注册
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10006001, "msg": getErrMsgByCode(10006001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10006002, "msg": getErrMsgByCode(10006002, None)}
        return postHttpResponse(requestData, responseData)

    userLogin = None
    reqBody = requestData["post_body"]
    if "login" not in reqBody:
        responseData = {"result": 10006003, "msg": getErrMsgByCode(10006003, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userLogin = reqBody["login"]

    resData = {}
    userObj = None
    try:
        userObj = userDB.objects.get(login=userLogin)
    except userDB.DoesNotExist:
        resData["registered"] = 0
        responseData = {"result": 0, "msg": "OK", "data": resData}
        return postHttpResponse(requestData, responseData)
    except Exception as err:
        responseData = {"result": 10006004, "msg": getErrMsgByCode(10006004, err)}
        return postHttpResponse(requestData, responseData)

    resData["registered"] = 1
    responseData = {"result": 0, "msg": "OK", "data": resData}
    return postHttpResponse(requestData, responseData)

@csrf_exempt
@api_view(["post"])
def userInfoBatchAdd(request):
    """
    用户信息--批量新增
    role: 9普通用户, 10管理员
    """
    requestData = postRequestParser(request)
    if requestData["success"] != 1:
        responseData = {"result": 10002001, "msg": getErrMsgByCode(10002001, None)}
        return postHttpResponse(requestData, responseData)

    if "user_info" not in requestData:
        responseData = {"result": 10002002, "msg": getErrMsgByCode(10002002, None)}
        return postHttpResponse(requestData, responseData)

    userLoginedInfo = requestData["user_info"]

    userLogin = None
    userPassword = None
    userNickName = None
    userDept = None
    userRole = None
    userLevel = None
    reqBodys = requestData["post_body"]

    if "userList" not in reqBodys:
        responseData = {"result": 10002010, "msg": getErrMsgByCode(10002010, None)}
        return postHttpResponse(requestData, responseData)
    else:
        userList = reqBodys["userList"]

    for reqBody in userList:

        if "login" not in reqBody:
            responseData = {"result": 10002003, "msg": getErrMsgByCode(10002003, None)}
            return postHttpResponse(requestData, responseData)
        else:
            userLogin = reqBody["login"]
        if "password" not in reqBody:
            responseData = {"result": 10002004, "msg": getErrMsgByCode(10002004, None)}
            return postHttpResponse(requestData, responseData)
        else:
            userPassword = make_password(reqBody["password"], "mds")
        if "nickname" not in reqBody:
            responseData = {"result": 10002005, "msg": getErrMsgByCode(10002005, None)}
            return postHttpResponse(requestData, responseData)
        else:
            userNickName = reqBody["nickname"]
        if "role" not in reqBody:
            responseData = {"result": 10002006, "msg": getErrMsgByCode(10002006, None)}
            return postHttpResponse(requestData, responseData)
        else:
            userRole = reqBody["role"]

        if userDB.objects.filter(login=userLogin):
            responseData = {"result": 10002007, "msg": getErrMsgByCode(10002007, None)}
            return postHttpResponse(requestData, responseData)

        if userRole == 11:
            if userLoginedInfo["role"] < 11:
                return postHttpResponse(requestData, {"result": 10002008, "msg": getErrMsgByCode(10002008, None)})
        elif userRole == 10:
            if userLoginedInfo["role"] < 10:
                return postHttpResponse(requestData, {"result": 10002008, "msg": getErrMsgByCode(10002008, None)})
        elif userRole == 9:
            if userLoginedInfo["role"] < 10:
                return postHttpResponse(requestData, {"result": 10002008, "msg": getErrMsgByCode(10002008, None)})
        else:
            pass

        savePoint = transaction.savepoint()
        try:
            userObj = userDB()
            userObj.login = userLogin
            userObj.password = userPassword
            userObj.nickname = userNickName
            userObj.role = userRole
            userObj.save()
        except Exception as err:
            transaction.savepoint_rollback(savePoint)
            responseData = {"result": 10002009, "msg": getErrMsgByCode(10002009, err)}
            return postHttpResponse(requestData, responseData)

        transaction.savepoint_commit(savePoint)

    responseData = {"result": 0, "msg": "OK"}
    return postHttpResponse(requestData, responseData)