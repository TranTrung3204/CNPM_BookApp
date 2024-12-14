from flask import render_template, Flask
from flask import request, redirect, url_for, session, jsonify
from flask_login import login_user, logout_user
import cloudinary.uploader
from bookapp import app, utils,login
from bookapp.models import UserRole,Book,BookCategory
from math import ceil

@app.route("/")
def index():
    kw = request.args.get('kw')
    prods = utils.load_books(kw)
    return render_template('index.html', products=prods)


@app.route("/register", methods=['get', 'post'])
def user_register():
    err_msg = ""
    if request.method.__eq__('POST'):
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        avatar_path = None
        try:
            if password.strip().__eq__(confirm.strip()):
                avatar = request.files.get('avatar')
                if avatar:
                    res = cloudinary.uploader.upload(avatar)
                    avatar_path = res['secure_url']
                utils.add_user(name=name, username=username, password=password, email=email, avatar=avatar_path)
                return redirect(url_for('user_signin'))
            else:
                err_msg = 'passwords do not match'
        except Exception as ex:
            err_msg = "404 not found" + str(ex)

    return render_template('register.html', err_msg=err_msg)


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)

@app.route('/search', methods=['GET'])
def search():
    kw = request.args.get('kw', '')
    category_id = request.args.get('category_id', None)

    # Tìm kiếm theo tên sản phẩm hoặc danh mục
    products = Book.query

    # Tìm kiếm theo từ khóa tên sản phẩm
    if kw:
        products = products.filter(Book.name.ilike(f'%{kw}%'))

    # Tìm kiếm theo danh mục nếu có
    if category_id:
        products = products.filter(Book.category_id == category_id)

    # Chuyển sang danh sách
    products = products.all()

    # Lấy danh sách các danh mục để hiển thị
    categories = utils.load_book_categories()

    return render_template('product_list.html', products=products, categories=categories, kw=kw)

@app.route('/category/<int:category_id>')
def filter_by_category(category_id):
    page = request.args.get('page', 1, type=int)
    per_page = 6

    # Đếm tổng số sản phẩm trong category
    total_products = Book.query.filter(Book.category_id == category_id).count()

    # Truy vấn sản phẩm theo category với phân trang
    products = Book.query.filter(Book.category_id == category_id) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    # Tính tổng số trang
    total_pages = max(1, ceil(total_products / per_page))

    # Luôn hiển thị phân trang nếu tổng số sản phẩm > 6
    return render_template('product_list.html',
                           products=products,
                           category_id=category_id,
                           categories=utils.load_book_categories(),
                           current_page=page if total_products > per_page else None,
                           total_pages=total_pages if total_products > per_page else None)


@app.route("/user-login", methods=['get', 'post'])
def user_signin():
    err_msg = ""
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = utils.check_login(username=username, password=password)
        if user:
            login_user(user=user)
            return redirect(url_for('index'))
        else:
            err_msg = 'Username or password is incorrect !!!'
    return render_template('login.html', err_msg=err_msg)

@app.route('/admin-login', methods=['post'])
def admin_login():
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = utils.check_login(username=username, password=password, user_role=UserRole.ADMIN)

    if user:
        login_user(user=user)
        return redirect('/admin')


@app.route("/user-logout")
def user_signout():
    logout_user()
    return redirect(url_for('user_signin'))


@app.route('/cart')
def cart():
    err_msg = ""
    cart = session.get('cart', {})
    return render_template('cart.html',
                           cart=cart,
                           err_msg=err_msg,
                           stats=utils.count_cart(session.get('cart')))

@app.route('/api/add-cart', methods=['post'])
def add_to_cart():
    data = request.json
    id = str(data.get('id'))
    name = data.get('name')
    price = float(data.get('price'))  # Ép kiểu thành float

    cart = session.get('cart', {})
    if not cart:
        cart ={}
    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            'id': id,
            'name': name,
            'price': price,  # Giá là float
            'quantity': 1
        }
    session['cart'] = cart

    return jsonify(utils.count_cart(cart))


@app.route('/api/update-cart', methods=['POST'])
def update_cart():
    data = request.json
    product_id = str(data.get('id'))
    change = data.get('change')

    cart = session.get('cart', {})

    if product_id in cart:
        new_quantity = cart[product_id]['quantity'] + change
        if new_quantity > 0:
            cart[product_id]['quantity'] = new_quantity
        else:
            del cart[product_id]

    session['cart'] = cart
    cart_stats = utils.count_cart(cart)
    updated_total = cart[product_id]['quantity'] * cart[product_id]['price'] if product_id in cart else 0

    return jsonify({
        'updated_quantity': cart[product_id]['quantity'] if product_id in cart else 0,
        'updated_total': updated_total,
        'cart_total_quantity': cart_stats['total_quantity'],
        'cart_total_price': cart_stats['total_amount']
    })


@app.route('/api/delete-cart', methods=['POST'])
def delete_cart():
    data = request.json
    product_id = str(data.get('id'))

    # Lấy giỏ hàng từ session
    cart = session.get('cart', {})

    # Xóa sản phẩm khỏi giỏ hàng
    if product_id in cart:
        del cart[product_id]

    # Lưu lại giỏ hàng đã cập nhật
    session['cart'] = cart

    # Tính lại tổng tiền và số lượng
    cart_stats = utils.count_cart(cart)

    return jsonify({
        'cart_total_quantity': cart_stats['total_quantity'],
        'cart_total_price': cart_stats['total_amount']
    })


@app.route('/api/pay', methods=['post'])
def pay():
    try:
        utils.add_receipt(session.get('cart'))
        del session['cart']
    except:
        return jsonify({'code': 400})

    return jsonify({'code': 200})

@app.route('/product-list')
def product_list():
    page = request.args.get('page', 1, type=int)  # Lấy số trang từ query string
    per_page = 6  # Số sản phẩm mỗi trang
    kw = request.args.get('kw', '').strip()  # Tìm kiếm theo từ khóa
    category_id = request.args.get('category_id', type=int)  # Lọc theo danh mục

    query = Book.query

    if kw:
        query = query.filter(Book.name.ilike(f"%{kw}%"))  # Tìm kiếm tên sách

    if category_id:
        query = query.filter(Book.category_id == category_id)  # Lọc danh mục

    total = query.count()  # Tổng số sản phẩm
    products = query.offset((page - 1) * per_page).limit(per_page).all()  # Phân trang
    total_pages = max(1, ceil(total / per_page))  # Tính tổng số trang (ít nhất là 1)

    return render_template(
        'product_list.html',
        products=products,
        current_page=page,
        total_pages=total_pages,  # Truyền `total_pages` tới template
        categories=utils.load_book_categories()
    )


@app.context_processor
def common_response():
    return {
        'categories': utils.load_book_categories(),
        'cart_stats': utils.count_cart(session.get('cart',{}))
    }



if __name__ == '__main__':
    from bookapp.admin import *
    app.run(debug=True)
#abc