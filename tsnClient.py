import uuid

from loguru import logger

from TiShiNengError import TiShiNengError
from TiShiNengSdkPrivate import TiShiNengPrivate
from TiShiNengSdkPublic import TiShiNengSdkPublic
from database import get_db
from deviceModel import deviceModel
from models import TsnAccount_Model
from services.tsnAccount.tsnAccountDao import updateAccessToken, getTsnAccountByid, getTsnAccountByUid, addTsnAccount
from services.tsnSchool.tsnSchoolDao import getSchoolBySchoolId


async def getPublicVersionClient(accountModel: TsnAccount_Model):
    schoolId = accountModel.school_id
    uid = accountModel.user_id
    schoolCode = accountModel.school.school_code
    openId = accountModel.school.open_id
    lan_url = accountModel.school.lan_url
    deviceId = accountModel.mobile_device_id
    brandName = deviceModel.brand
    deviceNum = deviceModel.model
    osVersion = deviceModel.osver
    a_list = deviceModel.a_list
    access_token = accountModel.access_token
    fresh_token = accountModel.refresh_token
    username = accountModel.username
    password = accountModel.password
    tsn = TiShiNengSdkPublic(uid, schoolId, schoolCode, openId, deviceId, brandName, deviceNum, osVersion, access_token,
                             a_list)
    if lan_url != '' and lan_url is not None:
        tsn.setCloudUrl(lan_url)
    try:
        freshTokenResp = await tsn.freshToken(fresh_token)
        logger.info(freshTokenResp)
        if 'msg' not in freshTokenResp:
            async for newDb in get_db():
                await updateAccessToken(accountModel.id, newDb, freshTokenResp['access_token'],
                                        freshTokenResp['refresh_token'], freshTokenResp['expires_in'])
            tsn.setToken(freshTokenResp['access_token'])
    except TiShiNengError as e:
        if e.code == 401:
            logger.info("token失效，重新获取")
            tokenResp = await tsn.getAccessToken(username, password)
            logger.info(tokenResp)
            if 'msg' not in tokenResp:
                async for newDb in get_db():
                    await updateAccessToken(accountModel.id, newDb, tokenResp['access_token'],
                                            tokenResp['refresh_token'], tokenResp['expires_in'])
                tsn.setToken(tokenResp['access_token'])
            else:
                raise TiShiNengError(tokenResp['msg'], 10001)
        else:
            raise e
    return tsn


async def getPrivateVersionClient(accountModel: TsnAccount_Model):
    schoolId = accountModel.school_id
    uid = accountModel.user_id
    schoolCode = accountModel.school.school_code
    openId = accountModel.school.open_id
    school_url = accountModel.school.school_url
    isOpenEncry = accountModel.school.is_open_encry
    deviceId = accountModel.mobile_device_id
    brandName = deviceModel.brand
    deviceNum = deviceModel.model
    access_token = accountModel.access_token
    username = accountModel.username
    password = accountModel.password
    tsn = TiShiNengPrivate(uid, schoolId, schoolCode, isOpenEncry, deviceId, brandName, deviceNum, access_token)
    tsn.setSchoolUrl(school_url)
    tsn.setAppId(openId)
    try:
        testTokenResp = await tsn.getStudentInfo()
        if testTokenResp is None:
            raise TiShiNengError("token失效", 401)
    except TiShiNengError as e:
        if e.code == 401 or e.message == '登录失效' or '学生信息系统不存在' in e.message:
            logger.info("token失效，重新获取")
            tokenResp = await tsn.appLogin(username, password)
            logger.info(tokenResp)
            async for newDb in get_db():
                await updateAccessToken(accountModel.id, newDb, tokenResp['token'], '2', 86399)
            tsn.setAccessToken(tokenResp['token'])
        else:
            raise e
    return tsn


async def getTsnClientById(accountId, session):
    account: TsnAccount_Model = await getTsnAccountByid(accountId, session)
    if account.school.sys_type == 2:
        return await getPublicVersionClient(account)
    elif account.school.sys_type == 1:
        return await getPrivateVersionClient(account)
    else:
        raise TiShiNengError("未知的系统类型", 10001)


async def getTsnClientByUid(uid, session):
    account: TsnAccount_Model = await getTsnAccountByUid(uid, session)
    if account.school.sys_type == 2:
        return await getPublicVersionClient(account)
    elif account.school.sys_type == 1:
        return await getPrivateVersionClient(account)
    else:
        raise TiShiNengError("未知的系统类型", 10001)


async def tsnPasswordAuthServer(schoolId, userName, password, session):
    schoolModel = await getSchoolBySchoolId(schoolId, session)
    if not schoolModel:
        raise TiShiNengError("学校不存在")
    brandName = deviceModel.brand
    deviceNum = deviceModel.model
    osVersion = deviceModel.osver
    a_list = deviceModel.a_list
    deviceId = str(uuid.uuid4())
    if schoolModel.isPublicVersion():
        tsn = TiShiNengSdkPublic(0, schoolId, schoolModel.school_code, schoolModel.open_id, deviceId, brandName,
                                 deviceNum, osVersion, "", a_list)
        if schoolModel.lan_url != '' and schoolModel.lan_url is not None:
            tsn.setCloudUrl(schoolModel.lan_url)
        loginResp = await tsn.getAccessToken(userName, password)
        logger.info(loginResp)
        if 'msg' in loginResp:
            if 'Bad credentials' in loginResp['msg']:
                raise TiShiNengError("用户名错误")
            elif 'Wrong password.' in loginResp['msg']:
                raise TiShiNengError("密码错误")
            raise TiShiNengError(loginResp['msg'])
        accessToken = loginResp['access_token']
        refreshToken = loginResp['refresh_token']
        expiresIn = loginResp['expires_in']
        uid = loginResp['user_id']
        del tsn
        tsn = TiShiNengSdkPublic(uid, schoolId, schoolModel.school_code, schoolModel.open_id, deviceId, brandName,
                                 deviceNum, osVersion, accessToken, a_list)
        if schoolModel.lan_url != '' and schoolModel.lan_url is not None:
            tsn.setCloudUrl(schoolModel.lan_url)
        userInfo = await tsn.getLoginUserInfo()
        logger.info(userInfo)
        tsnAccountModel = await getTsnAccountByUid(uid, session)
        saveFlag = False
        if not tsnAccountModel:
            tsnAccountModel = TsnAccount_Model()
            saveFlag = True
        tsnAccountModel.student_id = userInfo['studentId']
        tsnAccountModel.user_id = uid
        tsnAccountModel.school_id = schoolId
        tsnAccountModel.username = userName
        tsnAccountModel.password = password
        tsnAccountModel.mobile_device_id = deviceId
        tsnAccountModel.access_token = accessToken
        tsnAccountModel.refresh_token = refreshToken
        tsnAccountModel.expires_in = expiresIn
        if saveFlag:
            await addTsnAccount(tsnAccountModel, session)
        else:
            await session.flush()
        return uid
    else:
        tsn = TiShiNengPrivate(0, schoolId, schoolModel.school_code, schoolModel.is_open_encry, deviceId, brandName,
                               deviceNum, "")
        tsn.setAppId(schoolModel.open_id)
        tsn.setSchoolUrl(schoolModel.school_url)
        loginResp = await tsn.appLogin(userName, password)
        logger.info(loginResp)
        userNum = loginResp['userNum']
        uid = loginResp['id']
        token = loginResp['token']
        del tsn
        tsnAccountModel = await getTsnAccountByUid(uid, session, schoolId)
        saveFlag = False
        if not tsnAccountModel:
            tsnAccountModel = TsnAccount_Model()
            saveFlag = True
        tsnAccountModel.student_id = userNum
        tsnAccountModel.user_id = uid
        tsnAccountModel.school_id = schoolId
        tsnAccountModel.username = userName
        tsnAccountModel.password = password
        tsnAccountModel.mobile_device_id = deviceId
        tsnAccountModel.access_token = token
        tsnAccountModel.refresh_token = ''
        tsnAccountModel.expires_in = 86399
        if saveFlag:
            await addTsnAccount(tsnAccountModel, session)
        else:
            await session.flush()
        sysUid = f'{schoolId}:{uid}'
        return sysUid
