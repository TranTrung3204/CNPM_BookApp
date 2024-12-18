
from bookapp.models import BookCategory,Book,User,Receipt, ReceiptDetail,UserRole
from bookapp import app, db
from flask_login import  current_user
from sqlalchemy import func
from sqlalchemy.sql import extract
import hashlib




def load_book_categories():
    categories = BookCategory.query.order_by('id').all()
    if not categories:
        return []  # Đảm bảo trả về danh sách rỗng nếu không có danh mục
    for category in categories:
        category.product_count = Book.query.filter(Book.category_id == category.id).count()
    return categories



def load_books(kw: object = None) -> object:
    products = Book.query
    if kw:
        products = products.filter(Book.name.contains(kw))
    return products.all()


def add_user(name, username, password, **kwargs):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = User(name=name.strip(),
                username=username.strip(),
                password=password,
                email=kwargs.get('email'),
                avatar=kwargs.get('avatar'))
    db.session.add(user)
    db.session.commit()

def search_books(kw):
    if not kw:
        return []
    # Bỏ khoảng trắng thừa, chuyển về chữ thường, tìm kiếm
    return Book.query.filter(
        Book.name.ilike(f"%{kw}%")
    ).all()

def load_books_by_category(category_id):
    return Book.query.filter(Book.category_id == category_id).all()

def load_book_categories():
    categories = BookCategory.query.order_by('id').all()
    for category in categories:
        category.product_count = Book.query.filter(Book.category_id == category.id).count()
    return categories


def check_login(username, password, user_role=UserRole.USER):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        return User.query.filter(User.username.__eq__(username.strip()),
                                 User.password.__eq__(password),
                                 User.user_role.__eq__(user_role)).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)

def count_cart(cart):
    total_quantity, total_amount = 0, 0
    if cart:
        for c in cart.values():
            c['price'] = float(c['price'])  # Chuyển price thành float
            c['quantity'] = int(c['quantity'])  # Chuyển quantity thành int
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['price']
    return {
        'total_quantity': total_quantity,
        'total_amount': total_amount
    }


def add_receipt(cart):
    if cart:
        receipt = Receipt(user=current_user)
        db.session.add(receipt)

        for c in cart.values():
            d = ReceiptDetail(receipt=receipt,
                              product_id=c['id'],
                              quantity=c['quantity'],
                              unit_price=c['price'])
            db.session.add(d)

        db.session.commit()





def products_stats(kw=None, from_date=None, to_date=None):
    p = db.session.query(
        Book.id,
        Book.name,
        func.sum(ReceiptDetail.quantity * ReceiptDetail.unit_price).label('total_price'))\
        .join(ReceiptDetail, ReceiptDetail.product_id == Book.id, isouter=True)\
        .join(Receipt, Receipt.id == ReceiptDetail.receipt_id)


    if kw:
        p = p.filter(Book.name.contains(kw))

    if from_date:
        p = p.filter(Receipt.created_date.__ge__(from_date))


    if to_date:
        p = p.filter(Receipt.created_date.__le__(to_date))


    p = p.group_by(Book.id)

    return p.all()

def product_month_stats(year):
    return db.session.query(extract('month', Receipt.created_date),
                            func.sum(ReceiptDetail.quantity*ReceiptDetail.unit_price))\
                        .join(ReceiptDetail, ReceiptDetail.receipt_id.__eq__(Receipt.id))\
                        .filter(extract('year', Receipt.created_date) == year)\
                        .group_by(extract('month', Receipt.created_date))\
                        .order_by(extract('month', Receipt.created_date)).all()