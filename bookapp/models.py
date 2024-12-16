from sqlalchemy.orm import relationship
from bookapp import db, app
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum
from datetime import datetime
from enum import Enum as UserEnum
from flask_login import UserMixin


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(UserEnum):
    ADMIN = 1
    USER = 2


class User(BaseModel, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    avatar = Column(String(50))
    email = Column(String(50))
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.now())
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    receipts = relationship('Receipt', backref='user', lazy=True)

    def __str__(self):
        return self.name


class BookCategory(BaseModel):
    name = Column(String(50), nullable=False, unique=True, )
    books = relationship('Book', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Book(BaseModel):
    name = Column(String(50), nullable=False)
    author = Column(String(50), nullable=True)
    description = Column(String(250), nullable=True)
    price = Column(Float, default=0)
    image = Column(String(250), nullable=True)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now())
    stock = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey(BookCategory.id), nullable=False)
    receipt_details = relationship('ReceiptDetail', backref='book', lazy=True)

    def __str__(self):
        return self.name


class Receipt(BaseModel):
    created_date = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    details = relationship('ReceiptDetail', backref='receipt', lazy=True)


class ReceiptDetail(db.Model):
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey(Book.id), nullable=False, primary_key=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)

class BookImport(BaseModel):
    __tablename__ = 'book_imports'
    book_id = Column(Integer, ForeignKey('book.id'), nullable=False)
    quantity = Column(Integer, nullable=False)  # Số lượng nhập
    unit_price = Column(Float, nullable=False)  # Đơn giá
    import_date = Column(DateTime, default=datetime.now)  # Ngày nhập

    book = relationship('Book', backref='imports')  # Quan hệ với bảng Book

    def __init__(self, book_id, quantity, unit_price, import_date):
        self.book_id = book_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.import_date = import_date

class ImportEntry(BaseModel):
    __tablename__ = 'import_entries'
    book_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    import_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<ImportEntry {self.book_name} - {self.quantity}>'


class Regulation(BaseModel):
    __tablename__ = 'regulations'
    name = Column(String(100), nullable=False)  # Tên quy định
    value = Column(Float, nullable=False)  # Giá trị của quy định (e.g., số lượng tối thiểu)
    is_active = Column(Boolean, default=True)  # Tình trạng hoạt động (có hiệu lực hay không)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
