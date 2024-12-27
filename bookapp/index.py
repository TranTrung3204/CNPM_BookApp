from functools import wraps

from flask import render_template, Flask, flash
from flask import request, redirect, url_for, session, jsonify
from flask_login import login_user, logout_user, LoginManager, login_required
import cloudinary.uploader
from bookapp import app, utils,login
from bookapp.models import UserRole,Book,BookCategory
from math import ceil

@app.route("/")
def index():
    if current_user.is_authenticated and current_user.user_role == UserRole.ADMIN:
        return redirect(url_for('user_signin'))  # Chuyển hướng đến trang đăng nhập người dùng nếu là admin
    kw = request.args.get('kw')
    prods = utils.load_books(kw)
    return render_template('index.html', products=prods)


# Cấu hình LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user_signin'  # Trang đăng nhập nếu chưa đăng nhập

@app.route('/contact')
def contact():
    if current_user.is_authenticated and current_user.user_role == UserRole.ADMIN:
        return redirect(url_for('user_signin'))  # Chuyển hướng đến trang đăng nhập người dùng nếu là admin
    return render_template('contact.html')

@login_manager.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)# Decorator để kiể


@app.route("/register", methods=['GET', 'POST'])
def user_register():
    err_msg = ""
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        avatar_path = None
        try:
            if password.strip() == confirm.strip():
                avatar = request.files.get('avatar')
                if avatar:
                    res = cloudinary.uploader.upload(avatar)
                    avatar_path = res['secure_url']
                utils.add_user(name=name, username=username, password=password, email=email, avatar=avatar_path)
                return redirect(url_for('user_signin'))
            else:
                err_msg = 'Passwords do not match'
        except Exception as ex:
            err_msg = "404 not found: " + str(ex)

    return render_template('register.html', err_msg=err_msg)

@app.route("/user-login", methods=['GET', 'POST'])
def user_signin():
    err_msg = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = utils.check_login(username=username, password=password)
        if user:
            login_user(user=user)
            # Kiểm tra vai trò người dùng và chuyển hướng phù hợp
            if user.user_role == UserRole.ADMIN:
                return redirect(url_for('user_signin'))  # Chuyển hướng đến trang đăng nhập người dùng nếu là admin
            else:
                return redirect(url_for('index'))
        else:
            err_msg = 'Username or password is incorrect !!!'
    return render_template('login.html', err_msg=err_msg)


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = utils.check_login(username=username, password=password, user_role=[UserRole.ADMIN, UserRole.QLKHO])

        if user:
            login_user(user=user)
            return redirect('/admin')  # Chuyển hướng về trang admin
        else:
            flash('Đăng nhập không hợp lệ. Vui lòng kiểm tra lại thông tin.', 'error')

    return render_template('admin/login.html')  # Hiển thị trang đăng nhập admin


@app.route("/user-logout")
def user_signout():
    if current_user.is_authenticated and current_user.user_role == UserRole.ADMIN:
        return redirect(url_for('user_signin'))  # Chuyển hướng đến trang đăng nhập người dùng nếu là admin
    if 'cart' in session: # xoá giỏ hàng trước khi đăng xuất
        del session['cart']
    logout_user()
    return redirect(url_for('user_signin'))

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



@app.route('/cart')
def cart():
    if current_user.is_authenticated and current_user.user_role == UserRole.ADMIN:
        return redirect(url_for('user_signin'))  # Chuyển hướng đến trang đăng nhập người dùng nếu là admin
    cart = session.get('cart', {})
    return render_template('cart.html', cart=cart, stats=utils.count_cart(cart))


@app.route('/api/add-cart', methods=['post'])
def add_to_cart():
    if not current_user.is_authenticated:
        return jsonify({
            'code': 401,
            'message': 'Vui lòng đăng nhập trước khi thêm sản phẩm vào giỏ hàng!'
        })

    data = request.json
    id = str(data.get('id'))
    name = data.get('name')
    price = float(data.get('price'))

    # Kiểm tra số lượng trong kho
    book = Book.query.get(id)
    if not book:
        return jsonify({
            'code': 404,
            'message': 'Sản phẩm không tồn tại!'
        })

    cart = session.get('cart', {})

    # Tính tổng số lượng hiện có trong giỏ
    current_quantity = cart[id]['quantity'] if id in cart else 0

    # Kiểm tra nếu thêm 1 sản phẩm nữa có vượt quá số lượng trong kho không
    if current_quantity + 1 > book.stock:
        return jsonify({
            'code': 400,
            'message': 'Số lượng sản phẩm trong kho không đủ!'
        })

    if id in cart:
        cart[id]['quantity'] += 1
    else:
        cart[id] = {
            'id': id,
            'name': name,
            'price': price,
            'quantity': 1
        }

    session['cart'] = cart
    return jsonify({
        'code': 200,
        'data': utils.count_cart(cart)
    })


@app.route('/api/update-cart', methods=['POST'])
def update_cart():
    data = request.json
    product_id = str(data.get('id'))
    change = data.get('change')

    cart = session.get('cart', {})

    # Kiểm tra số lượng trong kho
    book = Book.query.get(product_id)
    if not book:
        return jsonify({
            'code': 404,
            'message': 'Sản phẩm không tồn tại!'
        })

    if product_id in cart:
        new_quantity = cart[product_id]['quantity'] + change

        # Kiểm tra nếu số lượng mới vượt quá stock
        if new_quantity > book.stock:
            return jsonify({
                'code': 400,
                'message': 'Số lượng sản phẩm trong kho không đủ!',
                'available_stock': book.stock,
                'current_quantity': cart[product_id]['quantity']
            })

        if new_quantity > 0:
            cart[product_id]['quantity'] = new_quantity
        else:
            del cart[product_id]

    session['cart'] = cart
    cart_stats = utils.count_cart(cart)
    updated_total = cart[product_id]['quantity'] * cart[product_id]['price'] if product_id in cart else 0

    return jsonify({
        'code': 200,
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
        cart = session.get('cart')
        if not cart:
            return jsonify({'code': 400, 'error': 'Giỏ hàng trống!'})

        # Kiểm tra số lượng trong kho trước khi thanh toán
        for item in cart.values():
            book = Book.query.get(item['id'])
            if not book:
                return jsonify({'code': 400, 'error': f'Sản phẩm {item["name"]} không tồn tại!'})

            if book.stock < item['quantity']:
                return jsonify({
                    'code': 400,
                    'error': f'Sản phẩm {item["name"]} chỉ còn {book.stock} trong kho!'
                })

        data = request.json
        utils.add_receipt(
            cart=cart,
            delivery_method=data.get('delivery_method'),
            payment_method=data.get('payment_method'),
            delivery_address=data.get('delivery_address'),
            phone=data.get('phone'),
            email=data.get('email')
        )

        # Cập nhật số lượng trong kho
        for item in cart.values():
            book = Book.query.get(item['id'])
            book.stock -= item['quantity']

        db.session.commit()
        del session['cart']
        return jsonify({'code': 200})

    except Exception as e:
        db.session.rollback()
        print(str(e))
        return jsonify({'code': 400, 'error': str(e)})

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

@app.route('/submit_contact_form', methods=['POST'])
@login_required
def submit_contact_form():
    try:
        # Lấy dữ liệu từ biểu mẫu
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Log thông tin biểu mẫu (nếu cần)
        app.logger.info(f"Contact form submitted: Name={name}, Email={email}, Message={message}")

        # Trả về phản hồi JSON thành công
        return jsonify({'message': 'Gửi biểu mẫu thành công!'}), 200
    except Exception as e:
        # Ghi log lỗi
        app.logger.error(f"Error submitting contact form: {e}")
        return jsonify({'error': 'Đã xảy ra lỗi khi gửi biểu mẫu. Vui lòng thử lại sau.'}), 500


from flask import send_file
import io


@app.route('/export-stats/<int:month>/<int:year>')
@login_required
def export_stats(month, year):
    if not current_user.is_authenticated or current_user.user_role not in [UserRole.ADMIN, UserRole.QLKHO]:
        flash('Bạn không có quyền truy cập chức năng này!', 'error')
        return redirect(url_for('index'))

    try:
        # Lấy dữ liệu thống kê
        revenue_stats = utils.stats_by_category(month, year)
        book_stats = utils.stats_book_sold(month, year)
        total_revenue = sum(stat[1] for stat in revenue_stats) if revenue_stats else 0

        # Tạo file Excel
        wb = utils.export_stats_to_excel(revenue_stats, book_stats, month, year, total_revenue)

        # Lưu file vào buffer
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        # Tạo tên file
        filename = f"bao-cao-thang-{month}-nam-{year}.xlsx"

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Lỗi khi xuất báo cáo: {str(e)}', 'error')
        return redirect(url_for('admin.index'))

if __name__ == '__main__':
    from bookapp.admin import *
    app.run(debug=True)
#abc