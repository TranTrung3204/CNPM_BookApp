from bookapp.models import BookCategory,Book,User,Receipt, ReceiptDetail,UserRole
from bookapp import app, db
from flask_login import  current_user
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


def check_login(username, password, user_role=None):
    if username and password:
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        query = User.query.filter(User.username.__eq__(username.strip()),
                                  User.password.__eq__(password))

        if user_role:
            if isinstance(user_role, list):
                # Nếu user_role là list thì kiểm tra user có thuộc một trong các role đó không
                query = query.filter(User.user_role.in_(user_role))
            else:
                # Nếu user_role là giá trị đơn lẻ
                query = query.filter(User.user_role.__eq__(user_role))

        return query.first()


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
