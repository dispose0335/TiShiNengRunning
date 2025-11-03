from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from models import TsnAccount_Model


async def getTsnAccountByid(accountId, session) -> TsnAccount_Model:
    stmt = select(TsnAccount_Model).options(selectinload(TsnAccount_Model.school)).where(
        TsnAccount_Model.id == accountId)
    account = await session.execute(stmt)
    account = account.scalars().first()
    return account


async def getTsnAccountByUid(uid, session, schoolId=None) -> TsnAccount_Model:
    uid = str(uid)
    if ':' in uid:
        tmp = uid.split(':')
        uid = tmp[1]
        schoolId = tmp[0]
    stmt = select(TsnAccount_Model).options(selectinload(TsnAccount_Model.school)).where(
        TsnAccount_Model.user_id == uid)
    if schoolId:
        stmt = stmt.where(TsnAccount_Model.school_id == schoolId)
    account = await session.execute(stmt)
    account = account.scalars().first()
    return account


async def updateAccessToken(accountId, session, accessToken, refreshToken, expiresIn):
    stmt = update(TsnAccount_Model).where(TsnAccount_Model.id == accountId).values(
        access_token=accessToken,
        refresh_token=refreshToken,
        expires_in=expiresIn
    )
    await session.execute(stmt)
    await session.flush()
    return True


async def addTsnAccount(tsnAccountModel: TsnAccount_Model, session):
    session.add(tsnAccountModel)
    await session.flush()
    return tsnAccountModel.id
