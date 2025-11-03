import math
import random

from loguru import logger

EARTH_RADIUS_KM = 6371.009
METERS_PER_KM = 1000.0


class TsnRunPolyline:
    def __init__(self, points):
        """
        初始化 Polyline 对象
        :param geoData:
        """
        self.points = points
        self.distances = self.calculate_distances()
        self.total_length = sum(self.distances)

    def calculate_distances(self):
        """
        计算并储存每两个连续点之间的距离
        :return: List of distances
        """
        distances = []
        for i in range(len(self.points) - 1):
            distances.append(self.haversine_distance(self.points[i], self.points[i + 1]))
        return distances

    def haversine_distance(self, point1, point2):
        """
        计算两个经纬度点之间的 haversine 距离
        :param point1: (latitude1, longitude1)
        :param point2: (latitude2, longitude2)
        :return: 距离（米）
        """
        lon1, lat1 = point1
        lon2, lat2 = point2
        R = 6371000  # 地球半径，单位米
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def simulate_motion(self, avg_speed, distance):
        """
        模拟运动
        :param avg_speed: 平均移动速度（米/秒）
        :param distance: 总距离（米）
        :return: 行程过的所有 (latitude, longitude) 点
        """
        traveled_distance = 0
        current_path = self.points
        path_length = len(current_path)
        sampled_points = []
        current_point = current_path[0]
        path_index = 0
        minMillisecondInterval = 1000
        maxMillisecondInterval = 1300
        while traveled_distance < distance:
            # 生成随机速度
            millisecond_interval = random.randint(minMillisecondInterval, maxMillisecondInterval)
            time_interval = millisecond_interval / 1000
            speed_variation = random.uniform(0.6, 1)
            actual_speed = avg_speed * speed_variation
            motion_distance = actual_speed * time_interval  # 应行驶的距离

            accumulated_distance = 0

            while accumulated_distance < motion_distance and path_index < path_length - 1:
                next_point = current_path[path_index + 1]
                next_distance = self.haversine_distance(current_point, next_point)

                if accumulated_distance + next_distance < motion_distance:
                    accumulated_distance += next_distance
                    current_point = next_point
                    path_index += 1
                else:
                    # 需要在当前点和下一个点之间插值
                    excess_distance = motion_distance - accumulated_distance
                    ratio = excess_distance / next_distance
                    interpolated_point = self.interpolate_point(current_point, next_point, ratio)
                    sampled_points.append({
                        "lat": interpolated_point[1],
                        "lon": interpolated_point[0],
                        "millisecond": millisecond_interval,
                        "speed": actual_speed,
                        "distance": motion_distance,
                    })
                    current_point = interpolated_point  # 将当前点更新为插值点
                    traveled_distance += motion_distance
                    break

            if path_index >= path_length - 1:
                current_path = list(reversed(current_path))
                path_index = 0
                current_point = current_path[0]
        logger.info(f"traveled_distance:{traveled_distance}")
        return sampled_points, traveled_distance

    def interpolate_point(self, point1, point2, ratio):
        """
        在两个点之间插值生成一个新点
        :param point1: 起点
        :param point2: 终点
        :param ratio: 插值比率（0 到 1 之间）
        :return: 插值生成的新 (latitude, longitude) 点
        """
        lon1, lat1 = point1
        lon2, lat2 = point2
        lat = lat1 + (lat2 - lat1) * ratio
        lon = lon1 + (lon2 - lon1) * ratio
        return lon, lat


def haversine_distance(lat1, lon1, lat2, lon2):
    # Calculate the haversine distance between two points given their latitude and longitude
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    d_lat = lat2_rad - lat1_rad
    d_lon = lon2_rad - lon1_rad

    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = EARTH_RADIUS_KM * c

    return distance_km * METERS_PER_KM


def getPointListDistance(pointList):
    tmpSum = 0
    for index in range(1, len(pointList)):
        pre = pointList[index - 1]
        cur = pointList[index]
        distance = haversine_distance(pre[1], pre[0], cur[1], cur[0])
        tmpSum += distance
    return tmpSum


def genTiShiNengRunPathRepeat(pointList, needDistance, startTimeStamp, planUseTime, isPublic=True):
    result = []
    avgSpeed = needDistance / planUseTime  # 平均速度 m/s
    tsnRunPolyline = TsnRunPolyline(pointList)
    simulateMotionData, sumDistance = tsnRunPolyline.simulate_motion(avgSpeed, needDistance)
    sumStepNum = 0
    sumMinStepNum = 0
    stepList = []
    currentStepTime = 0
    logger.info(f"needDistance:{needDistance},sumDistance:{sumDistance}")
    runTotalTime = 0
    for simulateMotionPoint in simulateMotionData:
        distance = simulateMotionPoint['distance']
        stepDistance = random.uniform(0.7, 0.9)
        stepNum = int(distance / stepDistance)
        speed = round(simulateMotionPoint['speed'], 9)
        sumMinStepNum += stepNum
        sumStepNum += stepNum
        usedMillisecond = simulateMotionPoint['millisecond']
        usedTime = usedMillisecond / 1000
        runTotalTime += usedTime
        if currentStepTime + usedTime > 60:
            stepList.append(sumMinStepNum)
            currentStepTime = 0
            sumMinStepNum = 0
        currentStepTime += usedTime
        lat = round(simulateMotionPoint['lat'], 15)
        lon = round(simulateMotionPoint['lon'], 15)

        if isPublic:
            tmp = {
                'a': lat,
                'c': int(runTotalTime),
                "e": sumStepNum,  # 步数
                "i": False,
                "l": 1,
                "o": lon,
                "s": speed,  # 速度
                "t": startTimeStamp + usedMillisecond,
                'distance': distance,
            }
        else:
            tmp = {
                "countTime": 0,
                "latitude": lat,
                "locationType": 1,
                "longitude": lon,
                "puase": False,
                "speed": speed,
                'stability': 0,
                "time": startTimeStamp + usedMillisecond,
                "distance": distance,
            }
        startTimeStamp += usedMillisecond
        result.append(tmp)
    stepList.append(sumMinStepNum)
    if not isPublic:
        result[-1]['puase'] = True
        result[-2]['puase'] = True
    else:
        lastC = result[-2]['c']
        lastE = result[-2]['e']
        result[-1]['c'] = lastC
        result[-1]['e'] = lastE
        result[-1]['i'] = True
        result[-2]['i'] = True

    return result, stepList, sumDistance
