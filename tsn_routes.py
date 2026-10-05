from __future__ import annotations
from typing import Dict, Optional
ROUTE_BY_TOKEN: Dict[str, str] = {'84e66a8b2fcf9bfd9840bd17a5dd38cb': 'https://m.boxkj.com/app/sch/listSchoolDatas', 'd6b92e37a9625a7bc4b4486ecb906b76': 'https://m.boxkj.com/app/sch/getSchoolById', '7d7f2d3627c76f56f26fb6f1e1b8fed1': 'https://m.boxkj.com/admin/studentAppUpdate/stuAppVersion2', 'fac59b800623b1146b41984c3c8df858': 'https://m.boxkj.com/admin/userAppLogFile/addLogData', '05dbfd8c595b3687f8351745f27c449b': 'https://a.tsnkj.com/', '7ff944758843f909e729065961954713': 'https://h.tsnkj.com/static/user_agreement_info.html', 'f16f7cfccc6d82a3a6ae248da4d16a1d': 'https://h.tsnkj.com/static/user_agreement.html', '7e9c6f977d2da2dbe67cd1005eaaf6e1': 'upms/sysSchool/getAppid', 'f2cefb5799dbc3a2fca980a7c30b8b09': 'upms/sysSchool/getAppSocketServer', '8f27a7ee3082fff7aa759b38c697857a': 'exercise/exerciseRecord/sumExerciseRecord', 'ea78c742acd5a3b5d88cea8b018ee05e': 'exercise/exerciseSetting/2a36d143/getSetting', '38c9640f6ff5813c5c109acfa894f550': 'exercise/exerciseExplanation/getExerciseExplanationV2', 'ad93462ddf9ffa8365e94742e8c6f09e': 'exercise/exerciseRecord/2a36d143/addExerciseRecord', '2e3c1cc7b254311b8ad82f2d2d2fb550': 'exercise/exerciseRecord/2a36d143/listExerciseRecord', 'e40355ffec0e5271aa3515d1877263e8': 'exercise/exerciseRecord/2a36d143/getExerciseRecord', '70ba21ded261ce2933e968e14b32ef34': 'exercise/exerciseRecord/statisticsExerciseRecord', 'e813ce47703893c5be40802067a5472b': 'exercise/exerciseFeedback/addExerciseFeedback', 'e99908106a680b07ef8beee488dcf6cb': 'upms/basUserImage/addUserFace', 'c395524a1fcdcb89f13a8a352bb8ee7b': 'exercise/exerciseRunningFace/2a36d143/face', 'f4f56111c5a9899b708925cd66f39d4e': 'exercise/exerciseSetting/checkTimeOut', '42b54ea6aaaf0689c4a35414077d92bc': 'exercise/exerciseRunningFace/faceVer', 'fdd57c5a055c28fbaf8bdaa034c6cc23': 'exercise/exerciseSetting/2a36d143/getExerciseStartTime', 'ac3d2d0b50bcce8adf74696bb7452b52': 'app/stuGymClockRecord/addStuGymClockRecord', '785796286eb58ca15168713af4fce70c': 'auth/oauth/token', 'e5c6b9630a11efdfa31a4cfa4b227688': 'upms/app/listMenu', '7299e5cc759387e8eba523ca5ad16b56': 'upms/basUser/getLoginUserInfo', 'd60d116f2cd0fa1ff936d515b8a55f83': 'auth/token/logout', 'e8ed1c044ac961926d8f79bd70dee316': 'upms/messageArticle/listByType', '7a4b002c14f6cf723035e7ebbb6d91ce': 'upms/basUser/isDefalutPass', '21eac57f6453f133c23636f1001cfec5': 'exercise/exerciseFeedback/getFeedbackBalance', 'c9aab1c07f7f73d7598e9ac13361c663': 'upms/messageNotice/getLatestUnreadNotice', 'd44b2b293b348070162b31ea5d139130': 'upms/messageNotice/getMessageNoticeVoById', '8d4bbeb78ddde6cd39874081d49f1989': 'upms/basUser/getLoginUserInfoThird', '5b4b6be878dca78c15579ef99b9fb774': 'upms/messageArticleClickRecord/appClickArticle', 'c1107b22d1b83779cda4c4392c7c1cb6': 'https://www.pgyer.com/apiv2/app/check', '746bb441d7c9966c2f2c05284bb4e277': 'exercise/exerciseRecord/checkExerciseRecord', '595161576dff77f4a803c0ed91716d76': 'http://circle.h5.tsnkj.com/circle/circleRecord/appGetCircleH5Url', '75023684c498bc2726f8e691060ffecb': 'upms/app/getH5Url', '16dd77786f3c3e1ac964437c978434ef': 'upms/sysSchool/getSchoolDetail', 'fa7e67fe9e95d3f60e6195b7e28dd8fd': 'exercise/exerciseSetting/getExerciseQuestion', '02941f2e7a00142dbf74699df84b52dd': 'upms/app/getWeather', '51f3f9d9b6c4443621b37fa740c82fb8': 'upms/app/saveWeather', 'f924a2407811f3ba790d8816a27fa03d': 'exercise/exerciseSetting/sendFace2DeviceResult'}
ROUTE_NAMES: Dict[str, str] = {'defaultBaseUrl': '05dbfd8c595b3687f8351745f27c449b', 'userAgreementInfo': '7ff944758843f909e729065961954713', 'userAgreement': 'f16f7cfccc6d82a3a6ae248da4d16a1d', 'searchSchool': '84e66a8b2fcf9bfd9840bd17a5dd38cb', 'getSchoolById': 'd6b92e37a9625a7bc4b4486ecb906b76', 'appVersion': '7d7f2d3627c76f56f26fb6f1e1b8fed1', 'uploadLog': 'fac59b800623b1146b41984c3c8df858', 'getAppid': '7e9c6f977d2da2dbe67cd1005eaaf6e1', 'getAppSocketServer': 'f2cefb5799dbc3a2fca980a7c30b8b09', 'sumExerciseRecord': '8f27a7ee3082fff7aa759b38c697857a', 'getExerciseSetting': 'ea78c742acd5a3b5d88cea8b018ee05e', 'getExerciseExplanation': '38c9640f6ff5813c5c109acfa894f550', 'addExerciseRecord': 'ad93462ddf9ffa8365e94742e8c6f09e', 'listExerciseRecord': '2e3c1cc7b254311b8ad82f2d2d2fb550', 'getExerciseRecord': 'e40355ffec0e5271aa3515d1877263e8', 'statisticsExerciseRecord': '70ba21ded261ce2933e968e14b32ef34', 'addExerciseFeedback': 'e813ce47703893c5be40802067a5472b', 'addUserFace': 'e99908106a680b07ef8beee488dcf6cb', 'exerciseRunningFace': 'c395524a1fcdcb89f13a8a352bb8ee7b', 'checkTimeOut': 'f4f56111c5a9899b708925cd66f39d4e', 'faceVer': '42b54ea6aaaf0689c4a35414077d92bc', 'getExerciseStartTime': 'fdd57c5a055c28fbaf8bdaa034c6cc23', 'addStuGymClockRecord': 'ac3d2d0b50bcce8adf74696bb7452b52', 'oauthToken': '785796286eb58ca15168713af4fce70c', 'listMenu': 'e5c6b9630a11efdfa31a4cfa4b227688', 'getLoginUserInfo': '7299e5cc759387e8eba523ca5ad16b56', 'logout': 'd60d116f2cd0fa1ff936d515b8a55f83', 'messageArticleListByType': 'e8ed1c044ac961926d8f79bd70dee316', 'isDefaultPass': '7a4b002c14f6cf723035e7ebbb6d91ce', 'getFeedbackBalance': '21eac57f6453f133c23636f1001cfec5', 'latestUnreadNotice': 'c9aab1c07f7f73d7598e9ac13361c663', 'messageNoticeById': 'd44b2b293b348070162b31ea5d139130', 'getLoginUserInfoThird': '8d4bbeb78ddde6cd39874081d49f1989', 'clickArticle': '5b4b6be878dca78c15579ef99b9fb774', 'appCheckUpdate': 'c1107b22d1b83779cda4c4392c7c1cb6', 'checkExerciseRecord': '746bb441d7c9966c2f2c05284bb4e277', 'circleH5Url': '595161576dff77f4a803c0ed91716d76', 'getH5Url': '75023684c498bc2726f8e691060ffecb', 'getSchoolDetail': '16dd77786f3c3e1ac964437c978434ef', 'getExerciseQuestion': 'fa7e67fe9e95d3f60e6195b7e28dd8fd', 'getWeather': '02941f2e7a00142dbf74699df84b52dd', 'saveWeather': '51f3f9d9b6c4443621b37fa740c82fb8', 'sendFace2DeviceResult': 'f924a2407811f3ba790d8816a27fa03d'}
DEFAULT_BASE_URL = ROUTE_BY_TOKEN['05dbfd8c595b3687f8351745f27c449b']

class UnknownRouteError(KeyError):
    pass

def resolve_token(name_or_token: str) -> str:
    if name_or_token in ROUTE_NAMES:
        return ROUTE_NAMES[name_or_token]
    if name_or_token in ROUTE_BY_TOKEN:
        return name_or_token
    raise UnknownRouteError(f'未知路由: {name_or_token}')

def route(name_or_token: str) -> str:
    return ROUTE_BY_TOKEN[resolve_token(name_or_token)]

def is_absolute(url: str) -> bool:
    return url.startswith('http://') or url.startswith('https://')

def normalize_base_url(url: Optional[str]) -> str:
    candidate = (url or '').strip()
    if not is_absolute(candidate):
        candidate = DEFAULT_BASE_URL
    if candidate.endswith('/'):
        return candidate
    return candidate + '/'

def build_url(base_url: str, name_or_token: str) -> str:
    return join_url(base_url, route(name_or_token))

def join_url(base_url: str, path: str) -> str:
    if is_absolute(path):
        return path
    return normalize_base_url(base_url).rstrip('/') + '/' + path.lstrip('/')

def all_routes() -> Dict[str, str]:
    return {name: ROUTE_BY_TOKEN[token] for name, token in ROUTE_NAMES.items()}
