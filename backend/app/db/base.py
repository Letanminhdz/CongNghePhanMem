from sqlalchemy.orm import DeclarativeBase


# Base: Lớp cơ sở khai báo (Declarative Base) mà tất cả các SQLAlchemy Models trong hệ thống sẽ kế thừa
class Base(DeclarativeBase):
    pass
