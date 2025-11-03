import hashlib
import io
import time
import urllib.parse

from loguru import logger

from AesUtils import AESCrypto
from RsaUtils import RSACrypto
from TiShiNengError import TiShiNengError
from TiShiNengSdkBase import TiShiNengSdkBase


class TiShiNengPrivate:
    def __init__(self, uid, schoolId, schoolCode, isOpenEncry, deviceId, brandName, deviceNum, token):
        self.uid = uid
        self.schoolCode = schoolCode
        self.isOpenEncry = isOpenEncry
        self.schoolId = schoolId
        self.deviceId = deviceId
        self.brandName = brandName
        self.deviceNum = deviceNum
        self.appId = '791f3afb1da44db3bd0c67ffdfb2394b'
        self.appSecret = 'e8167ef026cbc5e456ab837d9d6d9254'
        self.appSign = '7F:C0:22:E6:7C:7D:2A:CC:C3:C8:77:0A:46:13:8D:C3'
        self.schoolUrl = ''
        self.platform = '1'
        self.tiShiNengBaseClient = TiShiNengSdkBase(uid, schoolId, deviceId, brandName, deviceNum, token)
        self.versionName = self.tiShiNengBaseClient.versionName
        self.httpClient = self.tiShiNengBaseClient.getHttpClient()
        self.useXieQu = False
        self.token = token
        self.rsaUtils = RSACrypto(
            'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq4laolA7zAk7jzsqDb3Oa5pS/uCPlZfASK8Soh/NzEmry77QDZ2koyr96M5Wx+'
            'A9cxwewQMHzi8RoOfb3UcQO4UDQlMUImLuzUnfbk3TTppijSLH+PU88XQxcgYm2JTa546c7JdZSI6dBeXOJH20quuxWyzgLk9jAlt3ytYy'
            'gPQ7C6o6ZSmjcMgE3xgLaHGvixEVpOjL/pdVLzXhrMqWVAnB/snMjpCqesDVTDe5c6OOmj2q5J8n+tzIXtnvrkxQSDaUp8DWF8meMwyTE'
            'rmYklMXzKic2rjdYZpHh4x98Fg0Q28sp6i2ZoWiGrJDKW29mntVQQiDNhKDawb4B45zUwIDAQAB')

        self.headers = {
            'token': self.token,
            'channel': 'Android',
            'version': self.tiShiNengBaseClient.version,
            'type': '0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept-encoding': 'gzip',
            'user-agent': 'okhttp/4.9.0',
        }

    def isPublic(self):
        return False

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
    def getMd5(text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def getTokenAesEncrypt(self, text):
        md5Token = self.getMd5(self.token)
        key = md5Token[0:16]
        iv = md5Token[16:32]
        aesUtils = AESCrypto(key, iv)
        return aesUtils.encrypt(text)

    def setAccessToken(self, token):
        self.token = token
        self.headers = {
            'token': self.token,
            'channel': 'Android',
            'version': self.tiShiNengBaseClient.version,
            'type': '0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept-encoding': 'gzip',
            'user-agent': 'okhttp/4.9.0',
        }

    def setSchoolUrl(self, schoolUrl):
        if schoolUrl[-1] == '/':
            schoolUrl = schoolUrl[:-1]
        self.schoolUrl = schoolUrl

    def setAppId(self, appId):
        self.appId = appId

    def getEncryptAppId(self, timeStamp):
        text = self.appId + self.token + timeStamp
        return self.getMd5(self.getTokenAesEncrypt(text))

    def getEncryptAppSecret(self, timeStamp):
        text = self.token + timeStamp
        return self.getMd5(self.getTokenAesEncrypt(text))

    def getSign2(self, params: dict, timestamp: str):
        encryptAppId = self.getEncryptAppId(timestamp)
        encryptAppSecret = self.getEncryptAppSecret(timestamp)
        params.pop("sign", None)
        params.update({"appId": encryptAppId, "appSecret": encryptAppSecret})
        keys = list(params.keys())
        keys.sort()
        result = []
        for key in keys:
            value = params[key]
            result.append(self.kVtoStr(key, value, False))
        concatenated_string = "&".join(result)
        return self.getTokenAesEncrypt(concatenated_string)

    def getSign(self, params: dict):
        params.pop("sign", None)
        params.update({"appId": self.appId, "appSecret": self.appSecret})
        keys = list(params.keys())
        keys.sort()
        result = []
        for key in keys:
            value = params[key]
            result.append(self.kVtoStr(key, value, False))
        concatenated_string = "&".join(result)
        # logger.debug(concatenated_string)
        return self.getMd5(concatenated_string)

    async def httpPost(self, url, data):
        url = self.schoolUrl + url
        try:
            timestamp = str(int(time.time() * 1000))
            data['timestamp'] = timestamp
            if self.isOpenEncry and (
                    'app/sportRecordSetting/getSetting' in url or 'app/appSportRecord/appAddSportRecord' in url):
                sign = self.getSign2(data.copy(), timestamp)
            else:
                sign = self.getSign(data.copy())
            data['sign'] = sign
            headers = self.headers.copy()
            resp = await self.httpClient.post(url=url, data=data, headers=headers)
            if resp.status_code == 200:
                try:
                    resp = resp.json()
                except Exception as e:
                    logger.info(resp.text)
                if resp['returnCode'] == '200':
                    # logger.info(resp)
                    return resp['data']
                raise TiShiNengError(resp['returnMsg'])
            else:
                raise TiShiNengError(resp.text[:100], resp.status_code)
        except TiShiNengError as e:
            raise e

    async def findAllProvince(self):
        return await self.tiShiNengBaseClient.findAllProvince()

    async def listSchoolByProvinceId(self, provinceId):
        return await self.tiShiNengBaseClient.listSchoolByProvinceId(provinceId)

    async def getSchoolById(self, schoolId):
        return await self.tiShiNengBaseClient.getSchoolById(schoolId)

    async def addUploadRecord(self):
        return await self.tiShiNengBaseClient.addUploadRecord()

    async def stuAppVersion2(self):
        return await self.tiShiNengBaseClient.stuAppVersion2()

    async def getReplyFeedBackCountUser(self):
        return await self.tiShiNengBaseClient.getReplyFeedBackCountUser()

    async def appAnnouncementContentList(self):
        url = '/app/announcementContent/appAnnouncementContentList'
        params = {}
        return await self.httpPost(url, params)

    async def appLogin(self, username, password):
        url = '/app/appstu/login'
        encryptedPassword = self.rsaUtils.encrypt(password)
        params = {'uname': username, 'pwd': encryptedPassword}
        return await self.httpPost(url, params)

    async def noReadNotice(self):
        url = '/app/appnotice/noReadNotice'
        params = {
            "userId": self.uid,
            "identity": "0"
        }
        return await self.httpPost(url, params)

    async def ispwdmod(self, username):
        url = '/app/ispwdmod'
        params = {
            "userNum": username,
        }
        return await self.httpPost(url, params)

    async def appListNoticeData(self):
        url = '/app/appnotice/appListNoticeData'
        params = {
            "userId": self.uid,
            "identity": "0",
            "pageIndex": "1",
            "pageSize": "10",
        }
        return await self.httpPost(url, params)

    async def getStudentInfo(self):
        url = '/app/getStudentInfo'
        params = {}
        return await self.httpPost(url, params)

    async def getCampusList(self):
        url = '/app/syscampus/getCampusList'
        params = {}
        return await self.httpPost(url, params)

    async def getFieldByCampus(self, campusId):
        url = '/app/field/getFieldByCampus'
        params = {"campusId": campusId}
        return await self.httpPost(url, params)

    async def sumSportRecord(self):
        url = '/app/appSportRecord/sumSportRecord'
        params = {"userId": self.uid}
        return await self.httpPost(url, params)

    async def sportRecordSetting(self):
        url = '/app/sportRecordSetting/setting'
        params = {"uid": self.uid}
        return await self.httpPost(url, params)

    async def getSportSetting(self, runType=2):
        url = '/app/sportRecordSetting/getSetting'
        params = {"uid": self.uid, "runType": runType}
        return await self.httpPost(url, params)

    async def getSportSpecification(self, runType=2):
        url = '/app/appSportRecord/getSportSpecification'
        params = {"runType": runType}
        return await self.httpPost(url, params)

    async def getRunningStartTime(self, identify):
        url = '/app/sportRecordSetting/getRunningStartTime'
        params = {"identify": identify}
        return await self.httpPost(url, params)

    async def appSportRecordList(self, sportType=2, pageIndex=1, pageSize=10):
        url = '/app/appSportRecord/appSportRecordList'
        params = {
            "userId": self.uid,
            "sportType": str(sportType),
            "pageIndex": str(pageIndex),
            "pageSize": str(pageSize),
        }
        return await self.httpPost(url, params)

    async def getSportRecordId(self, sportRecordId):
        url = '/app/appSportRecord/getSportRecordId'
        params = {
            "sportRecordId": sportRecordId,
        }
        return await self.httpPost(url, params)

    async def appAddSportRecord(self, runType, startTime, endTime, gitudeLatitude, identify, formatSportTime,
                                formatSportRange, avgspeed, speed, okPointList, stepNumbers, isFaceStatus, points,
                                uploadType):
        url = '/app/appSportRecord/appAddSportRecord'
        params = {
            "userId": self.uid,
            "runType": runType,
            "startTime": startTime,
            "endTime": endTime,
            "gitudeLatitude": gitudeLatitude,
            "identify": identify,
            "formatSportTime": formatSportTime,
            "formatSportRange": formatSportRange,
            "avgspeed": avgspeed,
            "speed": speed,
            "okPointList": okPointList,
            "brand": self.brandName,
            "model": self.deviceNum,
            "system": "Android",
            "version": "13",
            "appVersion": self.versionName,
            "stepNumbers": stepNumbers,
            "isFaceStatus": isFaceStatus,
            "points": points,
            "uploadType": uploadType,
        }
        return await self.httpPost(url, params)

    async def appRuningFace(self, faceBytes: bytes, identify):
        url = self.schoolUrl + '/app/runingFace/appRuningFace'
        timestamp = str(int(time.time() * 1000))
        fileNames = f'avatar{timestamp}.png'
        data = {
            'userId': self.uid,
            'identify': identify,
            'timestamp': timestamp,
        }
        sign = self.getSign(data)
        headers = self.headers.copy()
        del headers['Content-Type']
        file = {
            'userId': (None, str(self.uid).encode(), 'multipart/form-data; charset=utf-8'),
            'identify': (None, identify.encode(), 'multipart/form-data; charset=utf-8'),
            'file': (fileNames, io.BytesIO(faceBytes), 'image/png'),
            'timestamp': (None, timestamp.encode(), 'multipart/form-data; charset=utf-8'),
            'sign': (None, sign.encode(), 'multipart/form-data; charset=utf-8'),
        }
        resp = await self.httpClient.post(url=url, files=file, headers=headers, timeout=30)
        if resp.status_code == 200:
            resp = resp.json()
            if int(resp['returnCode']) == 200:
                return resp['data']
            raise TiShiNengError(resp['returnMsg'])
        else:
            raise TiShiNengError(resp.text[:100], resp.status_code)
