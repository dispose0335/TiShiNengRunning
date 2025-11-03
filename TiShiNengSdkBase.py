import hashlib
import time
import urllib.parse

import httpx
from loguru import logger


class TiShiNengSdkBase:
    def __init__(self, uid, schoolId, deviceId, brandName, deviceNum, token):
        self.uid = uid
        self.schoolId = schoolId
        self.deviceId = deviceId
        self.brandName = brandName
        self.deviceNum = deviceNum
        self.appId = 'move'
        self.appSecret = 'e8167ef026cbc5e456ab837d9d6d9254'
        self.appSign = '7F:C0:22:E6:7C:7D:2A:CC:C3:C8:77:0A:46:13:8D:C3'
        self.apiUrl = 'https://m.boxkj.com'
        self.platform = '1'
        self.versionName = '2.0.16'
        self.version = '20160'
        self.httpClient = httpx.AsyncClient()
        self.token = token
        self.headers = {
            "Host": "m.boxkj.com",
            'token': self.token,
            'channel': 'Android',
            'version': self.version,
            'type': '0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept-encoding': 'gzip',
            'user-agent': 'okhttp/4.9.0'
        }

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

    def getSign(self, params: dict):
        params.update({"appId": 'move', "appSecret": self.appSecret})
        keys = list(params.keys())
        keys.sort()
        result = []

        for key in keys:
            value = params[key]
            result.append(self.kVtoStr(key, value, False))

        concatenated_string = "&".join(result)
        logger.debug(concatenated_string)
        return hashlib.md5(concatenated_string.encode()).hexdigest()

    async def httpPost(self, url, data):
        url = self.apiUrl + url
        try:
            data['timestamp'] = str(int(time.time() * 1000))
            sign = self.getSign(data.copy())
            data['sign'] = sign
            resp = await self.httpClient.post(url=url, data=data, headers=self.headers)
            if resp.status_code == 200:
                resp = resp.json()
                if resp['returnCode'] == '200':
                    return resp
                raise Exception(resp['returnMsg'])
            else:
                return None
        except Exception as e:
            logger.exception(e)
            return None

    async def findAllProvince(self):
        params = {}
        url = "/app/province/findAllProvince"
        return await self.httpPost(url, params)

    async def listSchoolByProvinceId(self, provinceId):
        params = {"provinceId": provinceId}
        url = "/app/sch/listSchoolByProvinceId"
        return await self.httpPost(url, params)

    async def getSchoolById(self, schoolId):
        params = {"schoolId": schoolId}
        url = "/app/sch/getSchoolById"
        return await self.httpPost(url, params)

    async def addUploadRecord(self):
        params = {
            "schoolId": self.schoolId,
            "platform": self.platform,
            "deviceId": self.deviceId,
            "brandName": self.brandName,
            "deviceNum": self.deviceNum,
            "sysUserId": "",
            "versionName": self.versionName
        }
        url = "/admin/analysis/addUploadRecord"
        return await self.httpPost(url, params)

    async def stuAppVersion2(self):
        params = {
            "schoolId": self.schoolId,
            "appSign": self.appSign
        }
        url = "/admin/studentAppUpdate/stuAppVersion2"
        return await self.httpPost(url, params)

    async def getReplyFeedBackCountUser(self):
        url = '/app/replyFeedBack/getReplyFeedBackCountUser'
        params = {"schoolId": self.schoolId, "userId": self.uid}
        return await self.httpPost(url, params)

    def getHttpClient(self):
        return self.httpClient
