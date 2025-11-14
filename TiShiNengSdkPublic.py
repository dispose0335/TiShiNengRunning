import base64
import hashlib
import io
import json
import time
import urllib.parse
import uuid
from typing import Dict, Any

from loguru import logger

from AesUtils import AESCrypto
from RsaUtils import RSACrypto
from TiShiNengError import TiShiNengError
from TiShiNengSdkBase import TiShiNengSdkBase


class TiShiNengSdkPublic:
    def __init__(self, uid, schoolId, schoolCode, openId, deviceId, brandName, deviceNum, osVersion, token, a_list):
        self.uid = uid
        self.schoolId = schoolId
        self.schoolCode = schoolCode
        self.deviceId = self.getMd5(deviceId)
        self.brandName = brandName
        self.deviceNum = deviceNum
        self.AndroidOsVersion = osVersion
        self.openId = openId
        self.appId = 'c9292ee89d2f49492f983f5931af0d09'
        self.appSecret = 'e8167ef026cbc5e456ab837d9d6d9254'
        self.appSign = '7F:C0:22:E6:7C:7D:2A:CC:C3:C8:77:0A:46:13:8D:C3'
        self.cloudUrl = 'http://a.sxstczx.com'
        self.platform = '1'
        self.tiShiNengBaseClient = TiShiNengSdkBase(uid, schoolId, deviceId, brandName, deviceNum, token)
        self.versionName = self.tiShiNengBaseClient.versionName
        self.httpClient = self.tiShiNengBaseClient.getHttpClient()
        self.token = token
        md5Token = self.getMd5(token)
        self.key = md5Token[0:16]
        self.iv = md5Token[16:32]
        self.aesUtils = AESCrypto(self.key, self.iv)
        self.passwordAesUtils = AESCrypto('thanks,pig4cloud', 'thanks,pig4cloud')
        self.rsaUtils = RSACrypto(
            'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgzQ7BYqBZ5LTjoOb9aHO8fI0hbww9YRW2lnqIdDyIjBwmhthTR+EmiKNm4yFKg6'
            'Vz2GW5ix3IdUQdaAq3ZZ7se/dCOTpu3dk15ZgkO6ZImUE7gqzSXXJ0NaACudk4yJwk3Q69kB4m3xIKxiOlG2HtbEed01LrUmLag9VOP96Bu'
            'Sao2sP4Als5hA/8C6KqdihTOcZF1RT+lqrT3Qvja7q+qI5QZw9d7NrFFycQs8jk8O49f9mkvLZRZCCWEbwzuCPTlMy/ZNAsMeU/gNSRKUnq'
            'uOiPboc2KUhsvY4cK0GeuS9vuIrMGE01L/BCc+rUrautq3n3WiIVJwnwWiJtgk33QIDAQAB')
        self.Cookie = 'host=' + self.schoolCode
        self.headers = {
            "model": f"{self.brandName}-{self.deviceNum}",
            "uniqueCode": self.deviceId,
            'school': self.schoolCode,
            'Cookie': self.Cookie,
            'accept-encoding': 'gzip',
            'user-agent': 'okhttp/4.9.0',
        }
        self.v2BaseDict = {
            "appType": "Android",
            "versionCode": int(self.tiShiNengBaseClient.version),
            "versionName": self.tiShiNengBaseClient.versionName,
            "signatureMD5": "7F:C0:22:E6:7C:7D:2A:CC:C3:C8:77:0A:46:13:8D:C3",
            "brand": self.brandName,
            "model": self.deviceNum,
            "system": "Android",
            "version": self.AndroidOsVersion,
            "uniqueCode": self.deviceId
        }
        self.a_list = a_list.split(',')

    def isPublic(self):
        return True

    @staticmethod
    def kVtoStr(key, value, is_encoded):
        if is_encoded:
            try:
                encoded_value = urllib.parse.quote(value)
                return f"{key}={encoded_value}"
            except Exception as e:
                return f"{key}={value}"
        else:
            return f"{key}={value}"

    @staticmethod
    def addNBy76Char(data):
        return '\n'.join([data[i:i + 76] for i in range(0, len(data), 76)]) + '\n'

    def getEncParams(self, randomAesUtils: AESCrypto, aesRandomKey: str, params: dict, is_encoded=False):

        appSignHash = "d2tnIyqximO/L8Y4MzfRELa1hSAtSRxzmvXlcOCzRyk="
        v = randomAesUtils.encrypt(appSignHash)
        params['v'] = v
        keys = list(params.keys())
        keys.sort()
        sorted_params = {key: params[key] for key in keys}
        logger.info(sorted_params)
        encData = randomAesUtils.encrypt(json.dumps(sorted_params, separators=(',', ':')))
        rsaEncryptedAesKey = self.rsaUtils.encrypt_bytes(aesRandomKey.encode())
        if not is_encoded:
            return {
                "key": rsaEncryptedAesKey.replace("+", " "),
                "param": encData.replace("+", " ")
            }
        else:
            return {
                "key": urllib.parse.quote(rsaEncryptedAesKey),
                "param": urllib.parse.quote(encData)
            }

    def getFaceEncParams(self, params: dict, timestamp: str):
        aesRandomKey = self.getMd5(self.token + timestamp)
        aesKey = aesRandomKey[0:16]
        randomAesUtils = AESCrypto(aesKey, None, True)
        appSignHash = "d2tnIyqximO/L8Y4MzfRELa1hSAtSRxzmvXlcOCzRyk="
        v = randomAesUtils.encrypt(appSignHash)
        params['v'] = v
        keys = list(params.keys())
        keys.sort()
        sorted_params = {key: params[key] for key in keys}
        logger.info(f"getFaceEncParams params={json.dumps(sorted_params)}")
        encData = randomAesUtils.encrypt(json.dumps(sorted_params, separators=(',', ':')))
        key = self.rsaUtils.encrypt_bytes(aesKey.encode())
        return {
            "key": key,
            "param": encData
        }

    @staticmethod
    def getMd5(text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def setCloudUrl(self, cloudUrl):
        # pass
        if "edu.cn" in cloudUrl:
            self.cloudUrl = cloudUrl
            host = cloudUrl.replace('http://', '').replace('https://', '')
            self.headers['Host'] = host

    def setToken(self, token):
        self.token = token
        md5Token = self.getMd5(token)
        self.key = md5Token[0:16]
        self.iv = md5Token[16:32]
        self.aesUtils = AESCrypto(self.key, self.iv)

    def getAesAppid(self, timeStamp):
        strText = self.appId + self.token + timeStamp
        return self.getMd5(self.aesUtils.encrypt(strText))

    def getAesAppSecret(self, timeStamp):
        strText = self.token + timeStamp
        return self.getMd5(self.aesUtils.encrypt(strText))

    def getSign(self, params: dict, timeStr):
        params.update(
            {"appId": self.getAesAppid(timeStr), "appSecret": self.getAesAppSecret(timeStr)})
        keys = list(params.keys())
        keys.sort()
        result = []
        for key in keys:
            value = params[key]
            result.append(self.kVtoStr(key, value, False))
        concatenated_string = "&".join(result)
        urlDecode = urllib.parse.unquote(concatenated_string)
        urlDecode = self.aesUtils.encrypt(urlDecode)
        return self.getMd5(urlDecode)

    def getFaceSign(self, params: dict, timeStr):
        for param in params:
            params[param] = params[param].replace('+', ' ')
        params.update(
            {"appId": self.getAesAppid(timeStr), "appSecret": self.getAesAppSecret(timeStr)})
        keys = list(params.keys())
        keys.sort()
        result = []
        for key in keys:
            value = params[key]
            result.append(self.kVtoStr(key, value, False))
        concatenated_string = "&".join(result)
        aesEncrypted = self.aesUtils.encrypt(concatenated_string)
        return self.getMd5(aesEncrypted)

    async def getAccessToken(self, username, password):
        encPassword = self.passwordAesUtils.encrypt(password, zero_padding=True)
        params = {
            'username': username,
            'password': encPassword,
            'grant_type': 'password',
            'type': 'app',
            'appType': "stuApp"
        }
        headers = self.headers.copy()
        token = self.schoolCode + ':pig'
        base64Token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
        headers['Authorization'] = 'Basic ' + base64Token
        url = f'{self.cloudUrl}/auth/oauth/token'
        resp = await self.httpClient.post(url, params=params, headers=headers)
        return resp.json()

    async def freshToken(self, freshToken):
        params = {
            'refresh_token': freshToken,
            'scope': 'server',
            'grant_type': 'refresh_token',
            'type': 'app',
            'appType': "stuApp"
        }
        headers = self.headers.copy()
        token = self.schoolCode + ':pig'
        base64Token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
        headers['Authorization'] = 'Basic ' + base64Token
        url = f'{self.cloudUrl}/auth/oauth/token'
        resp = await self.httpClient.post(url, params=params, headers=headers)
        return resp.json()

    async def httpPost(self, url, data, timestamp):
        url = self.cloudUrl + url
        try:
            sign = self.getSign(data.copy(), timestamp)
            headers = self.headers.copy()
            headers['sign'] = sign
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            headers['timestamp'] = timestamp
            headers['Authorization'] = 'Bearer ' + self.token
            resp = await self.httpClient.post(url=url, data=data, headers=headers)
            if resp.status_code == 200:
                resp = resp.json()
                if resp['code'] == 0:
                    if 'addExerciseRecord' in url:
                        if 'exerciseRecordId' in resp:
                            return resp['data'], resp['exerciseRecordId']
                        else:
                            return resp['data'], None
                    return resp['data']
                raise TiShiNengError(resp['msg'])
            else:
                resp = resp.json()
                logger.error(resp)
                raise TiShiNengError(resp['msg'], resp['code'])
        except TiShiNengError as e:
            raise e

    async def httpGet(self, url, params, timestamp=None):
        url = self.cloudUrl + url
        try:
            if timestamp is None:
                timestamp = str(int(time.time() * 1000))
            sign = self.getSign(params.copy(), timestamp)
            headers = self.headers.copy()
            headers['sign'] = sign
            headers['Authorization'] = 'Bearer ' + self.token
            headers['timestamp'] = timestamp
            logger.info(f"API请求: {url}, 参数: {params}")
            resp = await self.httpClient.get(url=url, params=params, headers=headers)
            logger.info(f"API响应状态码: {resp.status_code}")
            if resp.status_code == 200:
                resp_json = resp.json()
                logger.info(f"API响应内容: {resp_json}")
                if resp_json['code'] == 0:
                    return resp_json['data']
                raise TiShiNengError(resp_json['msg'])
            else:
                resp_json = resp.json()
                logger.error(resp_json)
                raise TiShiNengError(resp_json['msg'], resp_json['code'])
        except TiShiNengError as e:
            raise e

    async def getAppid(self):
        params = {}
        url = '/upms/sysSchool/getAppid'
        return await self.httpGet(url, params)

    async def listMenu(self, location=1):
        params = {
            'location': str(location),
        }
        url = '/upms/app/listMenu'
        return await self.httpGet(url, params)

    async def messageArticleListByType(self, mtype=4):
        params = {
            'type': str(mtype),
        }
        url = '/upms/messageArticle/listByType'
        return await self.httpGet(url, params)

    async def getLatestUnreadNotice(self):
        params = {}
        url = '/upms/messageNotice/getLatestUnreadNotice'
        return await self.httpGet(url, params)

    async def isDefalutPass(self):
        params = {}
        url = '/upms/basUser/isDefalutPass'
        return await self.httpGet(url, params)

    async def sumExerciseRecord(self):
        params = {}
        url = '/exercise/exerciseRecord/sumExerciseRecord'
        return await self.httpGet(url, params)

    async def getFeedbackBalance(self):
        params = {}
        url = '/exercise/exerciseFeedback/getFeedbackBalance'
        return await self.httpGet(url, params)

    async def statisticsExerciseRecord(self):
        params = {}
        url = '/exercise/exerciseRecord/statisticsExerciseRecord'
        return await self.httpGet(url, params)

    async def getExerciseSetting(self, runType, longitude, latitude):
        params = self.v2BaseDict.copy()
        params['runType'] = runType
        params['longitude'] = longitude
        params['latitude'] = latitude
        url = '/exercise/exerciseSetting/2a36d143/getSetting'
        timestamp = str(int(time.time() * 1000))
        aesRandomKey = self.getMd5(self.token + timestamp)
        aesKey = aesRandomKey[0:16]
        randomAesUtils = AESCrypto(aesKey, None, True)
        encParams = self.getEncParams(randomAesUtils, aesKey, params)
        data = await self.httpGet(url, encParams, timestamp)
        decData = randomAesUtils.decrypt(data)
        return json.loads(decData)

    async def getExerciseStartTime(self, identify):
        params = {
            'identify': identify,
        }
        url = '/exercise/exerciseSetting/2a36d143/getExerciseStartTime'
        return await self.httpGet(url, params)

    async def addExerciseRecord(self, sportType, startTime, endTime, sportTime, sportRange, speed, avgSpeed,
                                gitudeLatitude, stepNumbers, isSequencePoint, pointList, okPointList, isFaceStatus,
                                uploadType, identify, geofence, limitSpeed, limitStride, limitStepFrequency,
                                gpsDistance):
        """
        新参数：
            f: isFromMockProvider 0为真实数据 1为模拟数据
            m: isMock 0为真实数据 1为模拟数据
            h: location.locationQualityReport.isInstalledHighDangerMockApp  0为真实数据 1为模拟数据
            d: 是否开启开发者模式 0为真实数据 1为模拟数据
        """
        if not isinstance(limitSpeed, str):
            limitSpeed = f'{limitSpeed:.1f}'
        else:
            limitSpeed = f'{float(limitSpeed):.1f}'
        if not isinstance(limitStride, str):
            limitStride = f'{limitStride:.1f}'
        else:
            limitStride = f'{float(limitStride):.1f}'
        data = {
            "sportType": sportType,
            "startTime": startTime,
            "endTime": endTime,
            "sportTime": sportTime,
            "sportRange": sportRange,
            "speed": speed,
            "avgSpeed": avgSpeed,
            "appVersion": self.versionName,
            "stepNumbers": stepNumbers,
            "isSequencePoint": isSequencePoint,
            "gitudeLatitude": gitudeLatitude,
            "pointList": pointList,
            "okPointList": okPointList,
            "isFaceStatus": str(isFaceStatus),
            "uploadType": int(uploadType),  # =0
            "identify": identify,
            "geofence": geofence,
            "limitSpeed": limitSpeed,
            "limitStride": limitStride,
            "limitStepFrequency": str(limitStepFrequency),
            "gpsDistance": gpsDistance,
            "d": 0,
            "f": 0,
            "m": 0,
            "h": 0,
            "environment": self.getEnvData(),
        }
        params = self.v2BaseDict.copy()
        params.update(data)

        timestamp = str(int(time.time() * 1000))
        aesRandomKey = self.getMd5(self.token + timestamp)
        aesKey = aesRandomKey[0:16]
        randomAesUtils = AESCrypto(aesKey, None, True)
        encParams = self.getEncParams(randomAesUtils, aesKey, params, True)
        url = '/exercise/exerciseRecord/2a36d143/addExerciseRecord'
        encResp, exerciseRecordId = await self.httpPost(url, encParams, timestamp)
        logger.info(f"addExerciseRecord: {encResp}, {exerciseRecordId}")
        return encResp, exerciseRecordId

    async def getExerciseRecord(self, exerciseRecordId):
        params = {
            'exerciseRecordId': exerciseRecordId,
        }
        url = '/exercise/exerciseRecord/2a36d143/getExerciseRecord'
        return await self.httpGet(url, params)

    async def getExerciseExplanation(self):
        params = {}
        url = '/exercise/exerciseExplanation/getExerciseExplanationV2'
        return await self.httpGet(url, params)

    async def getLoginUserInfo(self):
        params = {}
        url = '/upms/basUser/getLoginUserInfo'
        return await self.httpGet(url, params)

    async def listExerciseRecord(self, runStatus=1, date='', datePageIndex=1):
        params = {
            'status': runStatus,
            'date': date,
            'datePageIndex': datePageIndex,
        }
        url = '/exercise/exerciseRecord/2a36d143/listExerciseRecord'
        return await self.httpGet(url, params)

    async def getAppSocketServer(self):
        params = {"basUserId": self.uid}
        url = '/upms/sysSchool/getAppSocketServer'
        return await self.httpGet(url, params)

    async def listBasUserImageFace(self):
        params = {"basUserId": self.uid}
        url = '/upms/basUserImage/listBasUserImageFace'
        return await self.httpGet(url, params)

    @staticmethod
    def calculate_checksum(data: Dict[str, Any]) -> str:
        """根据OPPO官方算法计算checksum

        Args:
            data: 不包含checksum字段的检测结果数据

        Returns:
            MD5校验和
        """
        # 创建副本并移除checksum字段
        temp_data = data.copy()
        temp_data.pop("checksum", None)

        # 转换为JSON字符串（确保格式一致）
        json_string = json.dumps(temp_data, separators=(',', ':'), ensure_ascii=False)

        # 计算MD5
        md5_hash = hashlib.md5(json_string.encode('utf-8')).hexdigest()

        return md5_hash

    def getEnvData(self):
        oppoData = {
            "auth": "success",
            "root": {
                "result": "false"
            },
            "selinux": {
                "result": "false",
                "detail": ["Enforcing\n"]
            },
            "xposed": {
                "result": "false"
            },
            "proxy": {
                "result": "false"
            },
            "vpn": {
                "result": "false"
            },
            "separation": {
                "result": "false"
            },
            "emulator": {
                "result": "false"
            },
            "ptrace": {
                "result": "false"
            },
            "frida": {
                "result": "false",
                "detail": []
            },
            "hook": {
                "result": "false",
                "detail": []
            },
            "breakpoint": {
                "result": "false",
                "detail": []
            },
            "nonce": str(uuid.uuid4()),
            "timestamp": str(int(time.time() * 1000))
        }
        # 计算checksum
        checksum = self.calculate_checksum(oppoData)
        oppoData["checksum"] = checksum
        safeData = {
            "sign": "true",
            "root": "false",
            "emulator": "false",
            "hook": "false",
            "debug": "false",
            "breakpoint": "false",
            "supported_abis": self.a_list
        }
        return {
            "deviceId": self.deviceId,
            "oppo": json.dumps(oppoData, separators=(',', ':')),
            "safe": json.dumps(safeData, separators=(',', ':')),
        }

    async def exerciseRunningFace(self, faceBytes: bytes, coordinates, identify, runType=1, faceType=1):
        url = self.cloudUrl + '/exercise/exerciseRunningFace/2a36d143/face'
        timestamp = str(int(time.time() * 1000))

        data = {
            "identify": identify,
            'type': str(faceType),
            "runType": str(runType),
            "coordinates": coordinates,
            "timeStamp": timestamp,
            "exception": "0",
            "environment": self.getEnvData(),
        }
        params = self.v2BaseDict.copy()
        params.update(data)
        encParams = self.getFaceEncParams(params, timestamp)
        key = encParams['key']
        param = encParams['param']
        sign = self.getFaceSign({'key': key, 'param': param}, timestamp)
        headers = self.headers.copy()
        headers['sign'] = sign
        headers['timestamp'] = timestamp
        headers['Authorization'] = 'Bearer ' + self.token
        file = {
            'key': (None, key.encode(), 'multipart/form-data; charset=utf-8'),
            'param': (None, param.encode(), 'multipart/form-data; charset=utf-8'),
            'file': ('file.jpg', io.BytesIO(faceBytes), 'image/png'),
        }
        resp = await self.httpClient.post(url=url, files=file, headers=headers, timeout=30)
        if resp.status_code == 200:
            resp = resp.json()
            logger.debug(resp)
            if resp['code'] == 0:
                return resp['data']
            raise TiShiNengError(resp['msg'])
        else:
            resp = resp.json()
            logger.error(resp)
            raise TiShiNengError(resp['msg'], resp['code'])
