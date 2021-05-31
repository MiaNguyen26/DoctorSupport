#chua table

from sqlalchemy import (
    func, Column, Table, String, Integer, SmallInteger,BigInteger,
    DateTime, Date, Boolean, Float,
    Index, ForeignKey,UniqueConstraint, event, __version__
)
import uuid
from sqlalchemy import or_,and_
from application.database import db
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.dialects.postgresql import UUID, JSONB


def default_uuid():
    return str(uuid.uuid4())

roles_users = db.Table('roles_users',
                db.Column('user_id', String(), db.ForeignKey('userinfo.id')),
                db.Column('role_id', String(), db.ForeignKey('role.id')))

class User(db.Model): #class doctor information, row = record
    __tablename__ = 'userinfo'
    id = db.Column(String(), primary_key=True, default=default_uuid) #default = tao key to phan biet record
    hoten = db.Column(String())
    tenkhongdau = db.Column(String())
    ngaysinh = db.Column(BigInteger())   #luu so giay : timestamp
    chungminhnhandan = db.Column(String)
    noilamviec = db.Column(String)
    email = db.Column(String(255), index=True)
    dienthoai = db.Column(String(), index=True) #index for searching doctor
    matkhau = db.Column(String(255))
    taikhoan  = db.Column(String(255), index=True)
    salt = db.Column(String()) #hard password

    active = db.Column(SmallInteger(), default=0) 
    vaitro = relationship("Role", secondary=roles_users) #admin or doctor
        
    # Methods
    def __repr__(self):
        """ Show user object info. """
        return '<User: {}>'.format(self.id)


    def has_role(self, role): #check user role
        if isinstance(role, str):
            return role in (role.vaitro for role in self.vaitro)
        else:
            return role in self.roles



class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(String(), primary_key=True,default=default_uuid) #primary_key = danh dau id la duy nhat, phan biet record
    vaitro = db.Column(String(200), unique=True) #unique=True -> chon 1 trong 2 role
    mota = db.Column(String) #hien thi Admin or Bac si
    active = db.Column(SmallInteger(), default=1) 

class FileInfo(db.Model): #upload file anh
    __tablename__ = 'fileinfo'
    id = db.Column(String, primary_key=True)
    name = db.Column(String, nullable=True)
    link = db.Column(String, nullable=True)
    description = db.Column(String, nullable=True)

class BenhNhan(db.Model):
    __tablename__ = 'benhnhan'
    id = db.Column(String, primary_key=True)
    hoten = db.Column(String)
    tenkhongdau = db.Column(String)
    ngaysinh = db.Column(BigInteger)
    gioitinh = db.Column(SmallInteger)#1 nam, 2 nu, 3 khac
    updated_at = db.Column(BigInteger)
    created_by = db.Column(String())
    benhan = db.Column(JSONB)
    
