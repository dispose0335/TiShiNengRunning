"""
SQLAlchemy 数据库模型定义
"""
import uuid

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RunPath(Base):
    """跑步路径记录表"""
    __tablename__ = "tsn_run_path"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_path_id = Column(String(100), unique=True, nullable=False, index=True, comment="跑步路径ID")
    school_code = Column(String(50), nullable=False, index=True, comment="学校代码")
    sport_range = Column(Float, nullable=False, comment="运动范围/距离")
    run_line_path = Column(Text, nullable=False, comment="跑步路线(JSON格式的GeoJSON)")
    point_id_list = Column(Text, nullable=True, comment="打卡点ID列表(JSON格式)")
    ok_point_list_json = Column(Text, nullable=True, comment="已打卡点列表(JSON格式)")
    is_public = Column(Boolean, default=True, comment="是否公开")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 创建复合索引
    __table_args__ = (
        Index('idx_school_code_run_path_id', 'school_code', 'run_path_id'),
    )

    def __repr__(self):
        return f"<RunPath(id={self.id}, run_path_id={self.run_path_id}, school_code={self.school_code})>"


def getUUID4Str():
    return str(uuid.uuid4())


class TsnAccount_Model(Base):
    __tablename__ = 'tsn_account'
    __table_args__ = (
        UniqueConstraint('user_id', 'school_id', name='user_id_school_id_unique'),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(String(64))
    user_id = Column(String(64), index=True)

    school_id = Column(Integer, ForeignKey('tsn_school.school_id'), nullable=False)
    school = relationship("TsnSchool_Model", overlaps="accounts")

    username = Column(String(64), nullable=False)
    password = Column(String(64), nullable=False)

    mobile_device_id = Column(String(128), default=getUUID4Str, nullable=False)

    access_token = Column(String(128), nullable=False)
    refresh_token = Column(String(128), nullable=False)
    expires_in = Column(Integer, nullable=False)

    auth_code = Column(String(128), default=getUUID4Str)


class TsnSchool_Model(Base):
    __tablename__ = 'tsn_school'

    id = Column(Integer, primary_key=True)
    school_id = Column(Integer, unique=True)

    accounts = relationship("TsnAccount_Model", overlaps="school")

    school_name = Column(String(128), nullable=False)
    school_url = Column(String(128), nullable=False)
    lan_url = Column(String(128))
    open_id = Column(String(128), nullable=False)
    is_open_keep = Column(Boolean, default=False)
    is_open_live = Column(Boolean, default=False)
    is_open_encry = Column(Boolean, default=False)
    sys_type = Column(Integer, nullable=False)
    school_code = Column(String(128), nullable=False)

    def isPublicVersion(self):
        return self.sys_type == 2
