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
    QLKHO = 3
    NHANVIEN = 4


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

class DeliveryMethod(UserEnum):
    HOME = "home"  # Giao hàng tận nhà
    STORE = "store"  # Nhận tại cửa hàng

class PaymentMethod(UserEnum):
    COD = "cod"  # Thanh toán khi nhận hàng
    ONLINE = "online"  # Thanh toán trực tuyến

class Receipt(BaseModel):
    created_date = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    delivery_method = Column(Enum(DeliveryMethod), nullable=False)  # Phương thức nhận hàng
    payment_method = Column(Enum(PaymentMethod), nullable=False)  # Phương thức thanh toán
    delivery_address = Column(String(255), nullable=True)  # Địa chỉ giao hàng (nếu có)
    phone = Column(String(15), nullable=False)  # Số điện thoại
    email = Column(String(50), nullable=True)  # Email (tùy chọn)
    details = relationship('ReceiptDetail', backref='receipt', lazy=True)

    def __str__(self):
        return f"Receipt {self.id} - User {self.user_id}"



class ReceiptDetail(db.Model):
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey(Book.id), nullable=False, primary_key=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)

class ImportEntry(BaseModel):
    __tablename__ = 'import_entries'
    book_id = Column(Integer, ForeignKey('book.id'), nullable=False)  # Thêm liên kết với Book
    book_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    import_date = Column(DateTime, default=datetime.now)

    # Thêm relationship với Book
    book = relationship('Book', backref='import_entries', lazy=True)

    def __repr__(self):
        return f'<ImportEntry {self.book_name} - {self.quantity}>'


class Regulation(BaseModel):
    __tablename__ = 'regulations'
    name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()
