from sqlalchemy import select, update

from models import TsnSchool_Model


async def addOrUpdateSchool(schoolId, schoolName, schoolUrl, lanUrl, openId, isOpenKeep, isOpenLive, isOpenEncry,
                            sys_type, school_code,
                            session):
    stmt = select(TsnSchool_Model).where(TsnSchool_Model.school_id == schoolId)
    school = await session.execute(stmt)
    school = school.scalars().first()
    if school:
        stmt = update(TsnSchool_Model).where(TsnSchool_Model.school_id == schoolId).values(
            school_name=schoolName,
            school_url=schoolUrl,
            lan_url=lanUrl,
            open_id=openId,
            is_open_keep=isOpenKeep,
            is_open_live=isOpenLive,
            is_open_encry=isOpenEncry,
            sys_type=sys_type,
            school_code=school_code
        )
        await session.execute(stmt)
        await session.flush()
    else:
        school = TsnSchool_Model(
            school_id=schoolId,
            school_name=schoolName,
            school_url=schoolUrl,
            lan_url=lanUrl,
            open_id=openId,
            is_open_keep=isOpenKeep,
            is_open_live=isOpenLive,
            is_open_encry=isOpenEncry,
            sys_type=sys_type,
            school_code=school_code
        )
        session.add(school)
        await session.flush()
    return school.id


async def getSchoolListDao(session, filterPublic=False) -> list[TsnSchool_Model]:
    stmt = select(TsnSchool_Model)
    if filterPublic:
        stmt = stmt.where(TsnSchool_Model.sys_type != 2)
    schoolList = await session.execute(stmt)
    schoolList = schoolList.scalars().all()
    return schoolList


async def getSchoolBySchoolId(schoolId, session) -> TsnSchool_Model:
    stmt = select(TsnSchool_Model).where(TsnSchool_Model.school_id == schoolId)
    school = await session.execute(stmt)
    school = school.scalars().first()
    return school
