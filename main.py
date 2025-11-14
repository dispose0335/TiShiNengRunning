#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TiShiNeng SDK Command Line Management System
Provides school updates, account authorization, and running tasks
"""
import asyncio
import uuid

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from TiShiNengSdkPrivate import TiShiNengPrivate
from database import get_db, init_db
from models import TsnAccount_Model
from services.tsnSchool.tsnSchoolDao import getSchoolListDao, addOrUpdateSchool
from tsnClient import tsnPasswordAuthServer, getTsnClientById
from tsnRunServer import TsnRunServer, TsnRunType
from spiderServer import startSpider


def getClient():
    tsn = TiShiNengPrivate(1, 1, '', False, str(uuid.uuid4()), 'Xiaomi',
                           '25053RT47C', "")
    return tsn


def getSchoolInfo(schoolCode):
    url = f"https://h.tsnkj.com/upms/sysSchool/getSchoolInfo?schoolCode={schoolCode}"
    resp = httpx.get(url, headers={
        "User-Agent": "okhttp/4.9.0",
    })
    resp = resp.json()
    return resp['data']


class TsnCliManager:
    """TiShiNeng CLI Manager"""

    def __init__(self):
        self.running = True

    def print_header(self, title: str):
        """Print header"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def print_menu(self):
        """Print main menu"""
        self.print_header("TiShiNeng 管理系统")
        print("1. 更新学校列表")
        print("2. 授权账号")
        print("3. 开始跑步")
        print("4. 爬取路径数据")
        print("5. 更新人脸图片")
        print("6. 查询跑步里程")
        print("0. 退出系统")
        print("=" * 60)

    async def update_school_list(self):
        """Update school list"""
        self.print_header("更新学校列表")
        print("正在从服务器获取学校列表，请稍候...")

        try:
            async for db in get_db():
                tsn = getClient()
                resp = await tsn.findAllProvince()

                if not resp or 'data' not in resp:
                    print("❌ 获取省份列表失败")
                    return

                provinces = resp['data']
                total_schools = 0

                for province in provinces:
                    province_name = province['province_name']
                    print(f"\n正在处理省份: {province_name}")

                    resp = await tsn.listSchoolByProvinceId(province['province_id'])
                    if not resp or 'data' not in resp:
                        continue

                    schools = resp['data']
                    for school in schools:
                        school_name = school['school_name']

                        # Skip demo and test schools
                        if 'demo' in school_name.lower() or 'test' in school_name.lower():
                            continue

                        # Get LAN URL for public version schools
                        lan_url = None
                        if school['sysType'] == '2':
                            try:
                                schoolInfo = getSchoolInfo(school['schoolCode'])
                                if schoolInfo:
                                    lan_url = schoolInfo.get('url')
                                    if lan_url:
                                        lan_url = f"https://{lan_url}"
                            except Exception as e:
                                logger.debug(f"Failed to get school info for {school_name}: {e}")

                        # Save to database
                        await addOrUpdateSchool(
                            school['school_id'],
                            school['school_name'],
                            school['school_url'],
                            lan_url,
                            school['openId'],
                            school['isOpenKeep'] == '1',
                            school['isOpenLive'] == '1',
                            school['isOpenEncry'] == '1',
                            int(school['sysType']),
                            school['schoolCode'],
                            db
                        )
                        total_schools += 1
                        print(f"  ✓ {school_name}")

                print(f"\n✅ 学校列表更新完成！共更新 {total_schools} 所学校")

        except Exception as e:
            logger.exception(e)
            print(f"❌ 更新失败: {str(e)}")

    async def authorize_account(self):
        """Authorize account"""
        self.print_header("授权账号")

        try:
            # 1. Select school
            async for db in get_db():
                schools = await getSchoolListDao(db)

                if not schools:
                    print("❌ 没有可用的学校，请先更新学校列表")
                    return

                print("\n请选择学校:")
                print("-" * 60)
                for idx, school in enumerate(schools, 1):
                    sys_type_name = "公版" if school.sys_type == 2 else "私版"
                    print(f"{idx}. {school.school_name} ({sys_type_name})")
                print("-" * 60)

                # Get user selection
                try:
                    choice = input("\n请输入学校编号 (0=取消): ").strip()
                    if choice == '0':
                        return

                    school_idx = int(choice) - 1
                    if school_idx < 0 or school_idx >= len(schools):
                        print("❌ 无效的学校编号")
                        return

                    selected_school = schools[school_idx]
                    print(f"\n已选择: {selected_school.school_name}")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 2. Input username and password
                print("\n" + "-" * 60)
                username = input("请输入用户名: ").strip()
                if not username:
                    print("❌ 用户名不能为空")
                    return

                password = input("请输入密码: ").strip()
                if not password:
                    print("❌ 密码不能为空")
                    return

                # 3. Perform authorization
                print("\n正在进行授权验证...")
                try:
                    uid = await tsnPasswordAuthServer(
                        selected_school.school_id,
                        username,
                        password,
                        db
                    )

                    print(f"\n✅ 授权成功！")
                    print(f"用户ID: {uid}")
                    print(f"学校: {selected_school.school_name}")

                except Exception as e:
                    logger.exception(e)
                    print(f"❌ 授权失败: {str(e)}")

        except Exception as e:
            logger.exception(e)
            print(f"❌ 操作失败: {str(e)}")

    async def start_running(self):
        """Start running"""
        self.print_header("开始跑步")

        try:
            async for db in get_db():
                # 1. Select account
                stmt = select(TsnAccount_Model).options(
                    selectinload(TsnAccount_Model.school)
                )
                result = await db.execute(stmt)
                accounts = result.scalars().all()

                if not accounts:
                    print("❌ 没有可用的账号，请先授权账号")
                    return

                print("\n请选择账号:")
                print("-" * 60)
                for idx, account in enumerate(accounts, 1):
                    school_name = account.school.school_name if account.school else "未知学校"
                    print(f"{idx}. {account.username} - {school_name}")
                print("-" * 60)

                # Get account selection
                try:
                    choice = input("\n请输入账号编号 (0=取消): ").strip()
                    if choice == '0':
                        return

                    account_idx = int(choice) - 1
                    if account_idx < 0 or account_idx >= len(accounts):
                        print("❌ 无效的账号编号")
                        return

                    selected_account = accounts[account_idx]
                    print(f"\n已选择账号: {selected_account.username}")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 2. Select run type
                print("\n请选择跑步类型:")
                print("-" * 60)
                print("1. 晨跑 (Morning Run)")
                print("2. 阳光跑 (Sun Run)")
                print("3. 自由跑 (Freedom Run)")
                print("-" * 60)

                run_type_map = {
                    '1': TsnRunType.morningRun,
                    '2': TsnRunType.sumRun,
                    '3': TsnRunType.freedom
                }

                run_type_name_map = {
                    '1': '晨跑',
                    '2': '阳光跑',
                    '3': '自由跑'
                }

                try:
                    run_choice = input("\n请输入跑步类型编号 (0=取消): ").strip()
                    if run_choice == '0':
                        return

                    if run_choice not in run_type_map:
                        print("❌ 无效的跑步类型")
                        return

                    selected_run_type = run_type_map[run_choice]
                    print(f"已选择: {run_type_name_map[run_choice]}")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 3. Input distance
                print("\n" + "-" * 60)
                try:
                    distance_str = input("请输入跑步距离(公里，例如: 2.5): ").strip()
                    distance = float(distance_str)

                    if distance <= 0:
                        print("❌ 距离必须大于0")
                        return

                    if distance > 50:
                        print("❌ 距离过长，请输入合理的距离")
                        return

                    print(f"跑步距离: {distance}km")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 4. Confirm and start running
                print("\n" + "=" * 60)
                print("跑步任务信息:")
                print(f"  账号: {selected_account.username}")
                print(f"  学校: {selected_account.school.school_name}")
                print(f"  类型: {run_type_name_map[run_choice]}")
                print(f"  距离: {distance}km")
                print("=" * 60)

                confirm = input("\n确认开始跑步? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("已取消")
                    return

                # 5. Execute running
                print("\n开始执行跑步任务...")
                try:
                    run_server = TsnRunServer(
                        accountId=selected_account.id,
                        runKiloMeter=distance,
                        logRunType=selected_run_type
                    )

                    await run_server.startRunHandle()
                    print("\n✅ 跑步任务完成！")

                except Exception as e:
                    logger.exception(e)
                    print(f"\n❌ 跑步失败: {str(e)}")

        except Exception as e:
            logger.exception(e)
            print(f"❌ 操作失败: {str(e)}")

    async def update_face_images(self):
        """Update face images for an account"""
        self.print_header("更新人脸图片")

        try:
            async for db in get_db():
                # 1. Select account
                stmt = select(TsnAccount_Model).options(
                    selectinload(TsnAccount_Model.school)
                )
                result = await db.execute(stmt)
                accounts = result.scalars().all()

                if not accounts:
                    print("❌ 没有可用的账号，请先授权账号")
                    return

                print("\n请选择要更新人脸图片的账号:")
                print("-" * 60)
                for idx, account in enumerate(accounts, 1):
                    school_name = account.school.school_name if account.school else "未知学校"
                    print(f"{idx}. {account.username} - {school_name}")
                print("-" * 60)

                # Get account selection
                try:
                    choice = input("\n请输入账号编号 (0=取消): ").strip()
                    if choice == '0':
                        return

                    account_idx = int(choice) - 1
                    if account_idx < 0 or account_idx >= len(accounts):
                        print("❌ 无效的账号编号")
                        return

                    selected_account = accounts[account_idx]
                    school_name = selected_account.school.school_name if selected_account.school else "未知学校"
                    print(f"\n已选择账号: {selected_account.username} - {school_name}")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 2. Confirm and start updating face images
                print("\n" + "=" * 60)
                print("更新人脸图片任务信息:")
                print(f"  账号: {selected_account.username}")
                print(f"  学校: {school_name}")
                print(f"  说明: 将从服务器下载最新的人脸图片并保存到本地")
                print("=" * 60)

                confirm = input("\n确认开始更新? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("已取消")
                    return

                # 3. Execute face image update
                print("\n开始更新人脸图片...")
                try:
                    # Initialize TsnRunServer with dummy values since we only need the face functionality
                    run_server = TsnRunServer(
                        accountId=selected_account.id,
                        runKiloMeter=2.0,  # Dummy value
                        logRunType=TsnRunType.freedom  # Dummy value
                    )
                    
                    # Load account info
                    run_server.accountModel = selected_account
                    run_server.tsnClient = await getTsnClientById(selected_account.id, db)
                    run_server.isPublic = run_server.tsnClient.isPublic()

                    # Update face images
                    face_image_data = await run_server.getFaceImage()
                    
                    if face_image_data:
                        print("\n✅ 人脸图片更新完成！")
                    else:
                        print("\n⚠️ 未获取到人脸图片，请检查账号设置")

                except Exception as e:
                    logger.exception(e)
                    print(f"\n❌ 更新失败: {str(e)}")

        except Exception as e:
            logger.exception(e)
            print(f"❌ 操作失败: {str(e)}")

    async def crawl_paths(self):
        """Crawl running paths from account"""
        self.print_header("爬取路径数据")

        try:
            async for db in get_db():
                # 1. Select account
                stmt = select(TsnAccount_Model).options(
                    selectinload(TsnAccount_Model.school)
                )
                result = await db.execute(stmt)
                accounts = result.scalars().all()

                if not accounts:
                    print("❌ 没有可用的账号，请先授权账号")
                    return

                print("\n请选择要爬取的账号:")
                print("-" * 60)
                for idx, account in enumerate(accounts, 1):
                    school_name = account.school.school_name if account.school else "未知学校"
                    sys_type = "公版" if account.school and account.school.sys_type == 2 else "私版"
                    print(f"{idx}. {account.username} - {school_name} ({sys_type})")
                print("-" * 60)

                # Get account selection
                try:
                    choice = input("\n请输入账号编号 (0=取消): ").strip()
                    if choice == '0':
                        return

                    account_idx = int(choice) - 1
                    if account_idx < 0 or account_idx >= len(accounts):
                        print("❌ 无效的账号编号")
                        return

                    selected_account = accounts[account_idx]
                    school_name = selected_account.school.school_name if selected_account.school else "未知学校"
                    print(f"\n已选择账号: {selected_account.username} - {school_name}")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 2. Confirm and start crawling
                print("\n" + "=" * 60)
                print("爬取任务信息:")
                print(f"  账号: {selected_account.username}")
                print(f"  学校: {school_name}")
                print(f"  说明: 将从该账号的历史运动记录中爬取路径数据")
                print("=" * 60)

                confirm = input("\n确认开始爬取? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("已取消")
                    return

                # 3. Execute spider
                print("\n开始爬取路径数据...")
                print("提示: 爬取过程可能需要一些时间，请耐心等待...\n")

                try:
                    await startSpider(selected_account.id)
                    print("\n✅ 路径数据爬取完成！")

                except Exception as e:
                    logger.exception(e)
                    print(f"\n❌ 爬取失败: {str(e)}")

        except Exception as e:
            logger.exception(e)
            print(f"❌ 操作失败: {str(e)}")

    async def query_running_distance(self):
        """Query running distance for an account"""
        self.print_header("查询跑步里程")

        try:
            async for db in get_db():
                # 1. Select account
                stmt = select(TsnAccount_Model).options(
                    selectinload(TsnAccount_Model.school)
                )
                result = await db.execute(stmt)
                accounts = result.scalars().all()

                if not accounts:
                    print("❌ 没有可用的账号，请先授权账号")
                    return

                print("\n请选择要查询的账号:")
                print("-" * 60)
                for idx, account in enumerate(accounts, 1):
                    school_name = account.school.school_name if account.school else "未知学校"
                    sys_type = "公版" if account.school and account.school.sys_type == 2 else "私版"
                    print(f"{idx}. {account.username} - {school_name} ({sys_type})")
                print("-" * 60)

                # Get account selection
                try:
                    choice = input("\n请输入账号编号 (0=取消): ").strip()
                    if choice == '0':
                        return

                    account_idx = int(choice) - 1
                    if account_idx < 0 or account_idx >= len(accounts):
                        print("❌ 无效的账号编号")
                        return

                    selected_account = accounts[account_idx]
                    school_name = selected_account.school.school_name if selected_account.school else "未知学校"
                    sys_type = "公版" if selected_account.school and selected_account.school.sys_type == 2 else "私版"
                    print(f"\n已选择账号: {selected_account.username} - {school_name} ({sys_type})")

                except ValueError:
                    print("❌ 请输入有效的数字")
                    return

                # 2. Query running distance based on account type
                print("\n正在查询跑步里程...")
                try:
                    # Get TsnClient instance
                    tsn_client = await getTsnClientById(selected_account.id, db)
                    
                    total_distance = 0.0
                    record_count = 0
                    
                    if tsn_client.isPublic():
                        # Public version (公版)
                        # Get summary
                        try:
                            summary = await tsn_client.sumExerciseRecord()
                            if summary and 'sportRange' in summary:
                                total_distance = float(summary['sportRange'])
                                record_count = int(summary.get('sportTimes', 0))
                        except Exception as e:
                            logger.exception(e)
                            print(f"⚠️ 获取公版汇总数据失败: {str(e)}")
                            
                        # Get detailed records
                        if total_distance == 0.0:
                            try:
                                page = 1
                                last_record_ids = set()  # Track record IDs to prevent duplicates
                                while True:
                                    records = await tsn_client.listExerciseRecord(runStatus=1, datePageIndex=page)
                                    if not records or 'records' not in records:
                                        break
                                        
                                    record_list = records['records']
                                    if not record_list:
                                        break
                                        
                                    # Check for duplicate records
                                    current_record_ids = set()
                                    has_new_records = False
                                    for record in record_list:
                                        record_id = record.get('id', '')
                                        current_record_ids.add(record_id)
                                        if record_id not in last_record_ids:
                                            has_new_records = True
                                            if 'sportRange' in record:
                                                total_distance += float(record['sportRange'])
                                        
                                    # If no new records, break the loop
                                    if not has_new_records:
                                        break
                                        
                                    record_count += len(record_list)
                                    last_record_ids.update(current_record_ids)
                                    page += 1
                                    
                                    # Limit pages to prevent infinite loop
                                    if page > 50:  # Max 50 pages
                                        break
                            except Exception as e:
                                logger.exception(e)
                                print(f"⚠️ 获取公版详细数据失败: {str(e)}")
                    else:
                        # Private version (私版)
                        # Get summary
                        try:
                            summary = await tsn_client.sumSportRecord()
                            if summary and 'sportRange' in summary:
                                total_distance = float(summary['sportRange'])
                                record_count = int(summary.get('sportTimes', 0))
                        except Exception as e:
                            logger.exception(e)
                            print(f"⚠️ 获取私版汇总数据失败: {str(e)}")
                            
                        # Get detailed records
                        if total_distance == 0.0:
                            try:
                                page = 1
                                last_record_ids = set()  # Track record IDs to prevent duplicates
                                while True:
                                    records = await tsn_client.appSportRecordList(sportType=2, pageIndex=page, pageSize=10)
                                    if not records or 'records' not in records:
                                        break
                                        
                                    record_list = records['records']
                                    if not record_list:
                                        break
                                        
                                    # Check for duplicate records
                                    current_record_ids = set()
                                    has_new_records = False
                                    for record in record_list:
                                        record_id = record.get('id', '')
                                        current_record_ids.add(record_id)
                                        if record_id not in last_record_ids:
                                            has_new_records = True
                                            if 'sportRange' in record:
                                                total_distance += float(record['sportRange'])
                                        
                                    # If no new records, break the loop
                                    if not has_new_records:
                                        break
                                        
                                    record_count += len(record_list)
                                    last_record_ids.update(current_record_ids)
                                    page += 1
                                    
                                    # Limit pages to prevent infinite loop
                                    if page > 50:  # Max 50 pages
                                        break
                            except Exception as e:
                                logger.exception(e)
                                print(f"⚠️ 获取私版详细数据失败: {str(e)}")

                    # Display results
                    print("\n" + "=" * 60)
                    print("跑步里程查询结果:")
                    print(f"  账号: {selected_account.username}")
                    print(f"  学校: {school_name}")
                    print(f"  类型: {sys_type}")
                    print(f"  总里程: {total_distance:.2f} 公里")
                    print(f"  记录数: {record_count} 条")
                    print("=" * 60)
                    print("\n✅ 查询完成！")

                except Exception as e:
                    logger.exception(e)
                    print(f"\n❌ 查询失败: {str(e)}")

        except Exception as e:
            logger.exception(e)
            print(f"❌ 操作失败: {str(e)}")

    async def run(self):
        """Run main program"""
        # Initialize database
        await init_db()

        print("\n欢迎使用 TiShiNeng 管理系统!")

        while self.running:
            self.print_menu()

            choice = input("\n请选择操作 (0-6): ").strip()

            if choice == '1':
                await self.update_school_list()
            elif choice == '2':
                await self.authorize_account()
            elif choice == '3':
                await self.start_running()
            elif choice == '4':
                await self.crawl_paths()
            elif choice == '5':
                await self.update_face_images()
            elif choice == '6':
                await self.query_running_distance()
            elif choice == '0':
                print("\n感谢使用，再见!")
                self.running = False
            else:
                print("\n❌ 无效的选项，请重新选择")

            if self.running:
                input("\n按 Enter 键继续...")


async def main():
    """Main function"""
    cli = TsnCliManager()
    await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        logger.exception(e)
        print(f"\n程序异常退出: {str(e)}")
