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
import tsn_environment
import tsn_routes
import tsn_payload

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
        self._environmentOverride = None
        self._envSignals = None
        self.appSignHash = tsn_payload.KNOWN_APP_SIGN_HASH
        self.rsaUtils = RSACrypto('MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgzQ7BYqBZ5LTjoOb9aHO8fI0hbww9YRW2lnqIdDyIjBwmhthTR+EmiKNm4yFKg6Vz2GW5ix3IdUQdaAq3ZZ7se/dCOTpu3dk15ZgkO6ZImUE7gqzSXXJ0NaACudk4yJwk3Q69kB4m3xIKxiOlG2HtbEed01LrUmLag9VOP96BuSao2sP4Als5hA/8C6KqdihTOcZF1RT+lqrT3Qvja7q+qI5QZw9d7NrFFycQs8jk8O49f9mkvLZRZCCWEbwzuCPTlMy/ZNAsMeU/gNSRKUnquOiPboc2KUhsvY4cK0GeuS9vuIrMGE01L/BCc+rUrautq3n3WiIVJwnwWiJtgk33QIDAQAB')
        self.Cookie = 'host=' + self.schoolCode
        self.headers = {'model': f'{self.brandName}-{self.deviceNum}', 'uniqueCode': self.deviceId, 'school': self.schoolCode, 'Cookie': self.Cookie, 'accept-encoding': 'gzip', 'user-agent': 'okhttp/4.9.0'}
        self.v2BaseDict = {'appType': 'Android', 'versionCode': int(self.tiShiNengBaseClient.version), 'versionName': self.tiShiNengBaseClient.versionName, 'signatureMD5': '7F:C0:22:E6:7C:7D:2A:CC:C3:C8:77:0A:46:13:8D:C3', 'brand': self.brandName, 'model': self.deviceNum, 'system': 'Android', 'version': self.AndroidOsVersion, 'uniqueCode': self.deviceId}
        self.a_list = a_list.split(',')

    def isPublic(self):
        return True

    @staticmethod
    def kVtoStr(key, value, is_encoded):
        if is_encoded:
            try:
                encoded_value = urllib.parse.quote(value)
                return f'{key}={encoded_value}'
            except Exception as e:
                return f'{key}={value}'
        else:
            return f'{key}={value}'

    @staticmethod
    def addNBy76Char(data):
        return '\n'.join([data[i:i + 76] for i in range(0, len(data), 76)]) + '\n'

    def getEncParams(self, randomAesUtils: AESCrypto, aesRandomKey: str, params: dict, is_encoded=False):
        appSignHash = self.appSignHash
        v = randomAesUtils.encrypt(appSignHash)
        params['v'] = v
        keys = list(params.keys())
        keys.sort()
        sorted_params = {key: params[key] for key in keys}
        logger.info(sorted_params)
        encData = randomAesUtils.encrypt(json.dumps(sorted_params, separators=(',', ':')))
        rsaEncryptedAesKey = self.rsaUtils.encrypt_bytes(aesRandomKey.encode())
        if not is_encoded:
            return {'key': rsaEncryptedAesKey.replace('+', ' '), 'param': encData.replace('+', ' ')}
        else:
            return {'key': urllib.parse.quote(rsaEncryptedAesKey), 'param': urllib.parse.quote(encData)}

    def getFaceEncParams(self, params: dict, timestamp: str):
        aesRandomKey = self.getMd5(self.token + timestamp)
        aesKey = aesRandomKey[0:16]
        randomAesUtils = AESCrypto(aesKey, None, True)
        appSignHash = self.appSignHash
        v = randomAesUtils.encrypt(appSignHash)
        params['v'] = v
        keys = list(params.keys())
        keys.sort()
        sorted_params = {key: params[key] for key in keys}
        logger.info(f'getFaceEncParams params={json.dumps(sorted_params)}')
        encData = randomAesUtils.encrypt(json.dumps(sorted_params, separators=(',', ':')))
        key = self.rsaUtils.encrypt_bytes(aesKey.encode())
        return {'key': key, 'param': encData}

    @staticmethod
    def getMd5(text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def setCloudUrl(self, cloudUrl):
        if not cloudUrl:
            return
        normalized = tsn_routes.normalize_base_url(cloudUrl)
        self.cloudUrl = normalized.rstrip('/')
        if 'edu.cn' in cloudUrl:
            parsed = urllib.parse.urlparse(normalized)
            if parsed.netloc:
                self.headers['Host'] = parsed.netloc

    def setToken(self, token):
        self.token = token
        md5Token = self.getMd5(token)
        self.key = md5Token[0:16]
        self.iv = md5Token[16:32]
        self.aesUtils = AESCrypto(self.key, self.iv)

    def setEnvironment(self, environment: dict | None):
        self._environmentOverride = dict(environment) if environment else None

    def setCertDer(self, cert_der: bytes | None):
        if cert_der:
            self.appSignHash = tsn_payload.app_sign_hash(bytes(cert_der))
        else:
            self.appSignHash = tsn_payload.KNOWN_APP_SIGN_HASH

    def setEnvSignals(self, signals):
        self._envSignals = signals

    def getOldSign(self, params: dict):
        return tsn_payload.old_sign(tsn_payload.build_auth_info(params), self.token)

    def getAesAppid(self, timeStamp):
        strText = self.appId + self.token + timeStamp
        return self.getMd5(self.aesUtils.encrypt(strText))

    def getAesAppSecret(self, timeStamp):
        strText = self.token + timeStamp
        return self.getMd5(self.aesUtils.encrypt(strText))

    def getSign(self, params: dict, timeStr):
        params.update({'appId': self.getAesAppid(timeStr), 'appSecret': self.getAesAppSecret(timeStr)})
        auth_info = tsn_payload.build_auth_info(params)
        urlDecode = urllib.parse.unquote(auth_info)
        urlDecode = self.aesUtils.encrypt(urlDecode)
        return self.getMd5(urlDecode)

    def getFaceSign(self, params: dict, timeStr):
        params.update({'appId': self.getAesAppid(timeStr), 'appSecret': self.getAesAppSecret(timeStr)})
        auth_info = tsn_payload.build_auth_info(params)
        aesEncrypted = self.aesUtils.encrypt(urllib.parse.unquote(auth_info))
        return self.getMd5(aesEncrypted)

    async def getAccessToken(self, username, password):
        encPassword = self.passwordAesUtils.encrypt(password, zero_padding=True)
        params = {'username': username, 'password': encPassword, 'grant_type': 'password', 'type': 'app', 'appType': 'stuApp'}
        headers = self.headers.copy()
        token = self.schoolCode + ':pig'
        base64Token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
        headers['Authorization'] = 'Basic ' + base64Token
        url = tsn_routes.join_url(self.cloudUrl, tsn_routes.route('oauthToken'))
        resp = await self.httpClient.post(url, params=params, headers=headers)
        return resp.json()

    async def freshToken(self, freshToken):
        params = {'refresh_token': freshToken, 'scope': 'server', 'grant_type': 'refresh_token', 'type': 'app', 'appType': 'stuApp'}
        headers = self.headers.copy()
        token = self.schoolCode + ':pig'
        base64Token = base64.b64encode(token.encode('utf-8')).decode('utf-8')
        headers['Authorization'] = 'Basic ' + base64Token
        url = tsn_routes.join_url(self.cloudUrl, tsn_routes.route('oauthToken'))
        resp = await self.httpClient.post(url, params=params, headers=headers)
        return resp.json()

    async def httpPost(self, url, data, timestamp):
        url = tsn_routes.join_url(self.cloudUrl, url)
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
                            return (resp['data'], resp['exerciseRecordId'])
                        else:
                            return (resp['data'], None)
                    return resp['data']
                raise TiShiNengError(resp['msg'])
            else:
                resp = resp.json()
                logger.error(resp)
                raise TiShiNengError(resp['msg'], resp['code'])
        except TiShiNengError as e:
            raise e

    async def httpGet(self, url, params, timestamp=None):
        url = tsn_routes.join_url(self.cloudUrl, url)
        try:
            if timestamp is None:
                timestamp = str(int(time.time() * 1000))
            sign = self.getSign(params.copy(), timestamp)
            headers = self.headers.copy()
            headers['sign'] = sign
            headers['Authorization'] = 'Bearer ' + self.token
            headers['timestamp'] = timestamp
            logger.info(f'API请求: {url}, 参数: {params}')
            resp = await self.httpClient.get(url=url, params=params, headers=headers)
            logger.info(f'API响应状态码: {resp.status_code}')
            if resp.status_code == 200:
                resp_json = resp.json()
                logger.info(f'API响应内容: {resp_json}')
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
        url = tsn_routes.route('getAppid')
        return await self.httpGet(url, params)

    async def listMenu(self, location=1):
        params = {'location': str(location)}
        url = tsn_routes.route('listMenu')
        return await self.httpGet(url, params)

    async def messageArticleListByType(self, mtype=4):
        params = {'type': str(mtype)}
        url = tsn_routes.route('messageArticleListByType')
        return await self.httpGet(url, params)

    async def getLatestUnreadNotice(self):
        params = {}
        url = tsn_routes.route('latestUnreadNotice')
        return await self.httpGet(url, params)

    async def isDefalutPass(self):
        params = {}
        url = tsn_routes.route('isDefaultPass')
        return await self.httpGet(url, params)

    async def sumExerciseRecord(self):
        params = {}
        url = tsn_routes.route('sumExerciseRecord')
        return await self.httpGet(url, params)

    async def getFeedbackBalance(self):
        params = {}
        url = tsn_routes.route('getFeedbackBalance')
        return await self.httpGet(url, params)

    async def statisticsExerciseRecord(self):
        params = {}
        url = tsn_routes.route('statisticsExerciseRecord')
        return await self.httpGet(url, params)

    async def getExerciseSetting(self, runType, longitude, latitude):
        params = self.v2BaseDict.copy()
        params['runType'] = runType
        params['longitude'] = longitude
        params['latitude'] = latitude
        url = tsn_routes.route('getExerciseSetting')
        timestamp = str(int(time.time() * 1000))
        aesRandomKey = self.getMd5(self.token + timestamp)
        aesKey = aesRandomKey[0:16]
        randomAesUtils = AESCrypto(aesKey, None, True)
        encParams = self.getEncParams(randomAesUtils, aesKey, params)
        data = await self.httpGet(url, encParams, timestamp)
        decData = randomAesUtils.decrypt(data)
        return json.loads(decData)

    async def getExerciseStartTime(self, identify):
        params = {'identify': identify}
        url = tsn_routes.route('getExerciseStartTime')
        return await self.httpGet(url, params)

    async def addExerciseRecord(self, sportType, startTime, endTime, sportTime, sportRange, speed, avgSpeed, gitudeLatitude, stepNumbers, isSequencePoint, pointList, okPointList, isFaceStatus, uploadType, identify, geofence, limitSpeed, limitStride, limitStepFrequency, gpsDistance, *, d=None, f=None, m=None, h=None, isValid=None, remarkId=None, setting=None, trackPoints=None, stepCount=None, elapsedSeconds=None, distanceMeters=None, userOpenDevelop=False, offline=0, environment=None):
        if not isinstance(limitSpeed, str):
            limitSpeed = f'{limitSpeed:.1f}'
        else:
            limitSpeed = f'{float(limitSpeed):.1f}'
        if not isinstance(limitStride, str):
            limitStride = f'{limitStride:.1f}'
        else:
            limitStride = f'{float(limitStride):.1f}'
        point_dicts = self._parse_track_points(trackPoints if trackPoints is not None else gitudeLatitude)
        extras = {}
        if setting is not None:
            extras = tsn_payload.build_submit_extras(setting, points=point_dicts, elapsed_s=float(elapsedSeconds if elapsedSeconds is not None else sportTime), distance_m=float(distanceMeters if distanceMeters is not None else float(sportRange) * 1000.0), steps=int(stepCount or 0), user_open_develop=userOpenDevelop, offline=offline, include_is_valid=isValid is None)
        else:
            extras = tsn_payload.aggregate_risk_flags(point_dicts, user_open_develop=userOpenDevelop, offline=offline)
        for key, value in (('d', d), ('f', f), ('m', m), ('h', h)):
            if value is not None:
                extras[key] = int(value)
        if isValid is not None:
            extras['isValid'] = int(isValid)
        if remarkId is not None:
            extras['remarkId'] = remarkId
        data = {'sportType': sportType, 'startTime': startTime, 'endTime': endTime, 'sportTime': sportTime, 'sportRange': sportRange, 'speed': speed, 'avgSpeed': avgSpeed, 'appVersion': self.versionName, 'stepNumbers': stepNumbers, 'isSequencePoint': isSequencePoint, 'gitudeLatitude': gitudeLatitude, 'pointList': pointList, 'okPointList': okPointList, 'isFaceStatus': str(isFaceStatus), 'uploadType': int(uploadType), 'identify': identify, 'geofence': geofence, 'limitSpeed': limitSpeed, 'limitStride': limitStride, 'limitStepFrequency': str(limitStepFrequency), 'gpsDistance': gpsDistance, 'd': extras.get('d', 0), 'f': extras.get('f', 0), 'm': extras.get('m', 0), 'h': extras.get('h', 0), 'environment': environment if environment is not None else self.getEnvData()}
        if 'isValid' in extras:
            data['isValid'] = extras['isValid']
        if 'remarkId' in extras:
            data['remarkId'] = extras['remarkId']
        params = self.v2BaseDict.copy()
        params.update(data)
        timestamp = str(int(time.time() * 1000))
        aesRandomKey = self.getMd5(self.token + timestamp)
        aesKey = aesRandomKey[0:16]
        randomAesUtils = AESCrypto(aesKey, None, True)
        encParams = self.getEncParams(randomAesUtils, aesKey, params, True)
        url = tsn_routes.route('addExerciseRecord')
        encResp, exerciseRecordId = await self.httpPost(url, encParams, timestamp)
        logger.info(f"addExerciseRecord: {encResp}, {exerciseRecordId}, flags={{d:{data['d']},f:{data['f']},m:{data['m']},h:{data['h']}}}, isValid={data.get('isValid')}, remarkId={data.get('remarkId')}")
        return (encResp, exerciseRecordId)

    @staticmethod
    def _parse_track_points(raw):
        if raw is None:
            return []
        if isinstance(raw, (list, tuple)):
            return [p for p in raw if isinstance(p, dict)]
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                return []
            if isinstance(parsed, list):
                return [p for p in parsed if isinstance(p, dict)]
        return []

    async def getExerciseRecord(self, exerciseRecordId):
        params = {'exerciseRecordId': exerciseRecordId}
        url = tsn_routes.route('getExerciseRecord')
        return await self.httpGet(url, params)

    async def getExerciseExplanation(self):
        params = {}
        url = tsn_routes.route('getExerciseExplanation')
        return await self.httpGet(url, params)

    async def getLoginUserInfo(self):
        params = {}
        url = tsn_routes.route('getLoginUserInfo')
        return await self.httpGet(url, params)

    async def listExerciseRecord(self, runStatus=1, date='', datePageIndex=1):
        params = {'status': runStatus, 'date': date, 'datePageIndex': datePageIndex}
        url = tsn_routes.route('listExerciseRecord')
        return await self.httpGet(url, params)

    async def getAppSocketServer(self):
        params = {'basUserId': self.uid}
        url = tsn_routes.route('getAppSocketServer')
        return await self.httpGet(url, params)

    async def listBasUserImageFace(self):
        params = {'basUserId': self.uid}
        url = '/upms/basUserImage/listBasUserImageFace'
        return await self.httpGet(url, params)

    @staticmethod
    def calculate_checksum(data: Dict[str, Any]) -> str:
        temp_data = data.copy()
        temp_data.pop('checksum', None)
        json_string = json.dumps(temp_data, separators=(',', ':'), ensure_ascii=False)
        md5_hash = hashlib.md5(json_string.encode('utf-8')).hexdigest()
        return md5_hash

    def getEnvData(self):
        if self._environmentOverride is not None:
            data = dict(self._environmentOverride)
            data.setdefault('deviceId', self.deviceId)
            return data
        return tsn_environment.build_environment_payload(device_id=self.deviceId, signals=self._envSignals, abis=self.a_list)

    async def exerciseRunningFace(self, faceBytes: bytes, coordinates, identify, runType=1, faceType=1):
        url = tsn_routes.join_url(self.cloudUrl, tsn_routes.route('exerciseRunningFace'))
        timestamp = str(int(time.time() * 1000))
        data = {'identify': identify, 'type': str(faceType), 'runType': str(runType), 'coordinates': coordinates, 'timeStamp': timestamp, 'exception': '0', 'environment': self.getEnvData()}
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
        file = {'key': (None, key.encode(), 'multipart/form-data; charset=utf-8'), 'param': (None, param.encode(), 'multipart/form-data; charset=utf-8'), 'file': ('file.jpg', io.BytesIO(faceBytes), 'image/png')}
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
