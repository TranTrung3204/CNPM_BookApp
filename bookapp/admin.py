from datetime import datetime
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from bookapp import db, app
from bookapp.models import BookCategory, Book, UserRole, Regulation, BookImport, ImportEntry
from flask_admin import BaseView, expose
from flask_login import current_user, logout_user, login_required
from flask import redirect, flash, url_for, request

admin = Admin(app=app, name="BookStore Management", template_mode="bootstrap4")


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class BookView(AuthenticatedModelView):
    # Kiểm tra lại các trường trong form_columns dưới dạng list
    column_list = ['name', 'author', 'description', 'price', 'image', 'active', 'created_date','stock', 'category']  # Hiển thị tên category
    form_columns = ['name', 'author', 'description', 'price', 'image', 'active', 'created_date', 'category_id']  # Người dùng chọn category
    column_labels = {
        'name': 'Book Name',
        'author': 'Author',
        'description': 'Description',
        'price': 'Price',
        'image': 'Image',
        'active': 'Active',
        'created_date': 'Created Date',
        'stock' : 'Stock',
        'category': 'Category'
    }


class BookCategoryView(AuthenticatedModelView):
    column_list = ['name']
    form_columns = ['name']
    column_labels = {
        'name': 'Category Name',
    }


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated






class BookImportView(BaseView):
    @expose('/')
    def index(self):
        # Lấy danh sách sách trong kho để hiển thị trong form
        books = Book.query.all()
        return self.render('admin/book_import.html', books=books)

    @expose('/add', methods=['POST'])
    def add_import(self):
        # Lấy quy định về số lượng nhập tối thiểu từ cơ sở dữ liệu
        min_quantity_value = self.get_min_quantity()
        max_stock_value = self.get_max_stock()
        # Lấy thông tin form nhập sách
        book_name = request.form.get('book_name')
        category_name = request.form.get('category_name')  # Lấy thể loại từ form
        quantity = self.get_integer_form_value('quantity')
        unit_price = self.get_float_form_value('unit_price')
        import_date = self.get_date_form_value('import_date')

        # Kiểm tra thông tin nhập vào
        if not book_name or not category_name or quantity is None or unit_price is None:
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
            return redirect(url_for('.index'))

        # 1. Kiểm tra xem thể loại sách đã tồn tại chưa, nếu chưa thì thêm mới
        category = BookCategory.query.filter_by(name=category_name).first()
        if not category:
            category = BookCategory(name=category_name)
            db.session.add(category)
            db.session.commit()

        # 2. Kiểm tra xem sách đã tồn tại trong kho chưa
        book = Book.query.filter_by(name=book_name).first()

        try:
            if book:
                # Nếu sách đã tồn tại, kiểm tra điều kiện số lượng
                if book.stock >= max_stock_value:
                    flash(f'Số lượng sách "{book_name}" trong kho đã đủ (>= {max_stock_value}). Không thể nhập thêm!',
                          'error')
                elif quantity < min_quantity_value:
                    flash(f'Số lượng nhập vào phải lớn hơn hoặc bằng {min_quantity_value}.', 'error')
                else:
                    # Cập nhật số lượng sách trong kho
                    book.stock += quantity
                    flash(f'Cập nhật số lượng sách "{book_name}" thành công!', 'success')
            else:
                # Nếu sách chưa tồn tại, tạo mới sách và thêm vào kho
                new_book = Book(
                    name=book_name,
                    author=None,  # Có thể để trống hoặc gán giá trị mặc định
                    description=None,  # Có thể để trống hoặc gán giá trị mặc định
                    price=unit_price,
                    stock=quantity,
                    category_id=category.id,  # Liên kết thể loại
                    created_date=import_date
                )
                db.session.add(new_book)
                flash(f'Tạo mới sách "{book_name}" thành công!', 'success')

            # 3. Lập phiếu nhập sách
            self.create_import_entry(book_name, quantity, unit_price, import_date)

            # Commit thay đổi vào cơ sở dữ liệu
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Hoàn tác thay đổi trong trường hợp lỗi
            flash(f'Đã xảy ra lỗi: {str(e)}', 'error')

        return redirect(url_for('.index'))

    def get_min_quantity(self):
        min_quantity = Regulation.query.filter_by(
            name='Số lượng nhập tối thiểu',
            is_active=True
        ).first()
        if not min_quantity:
            return 0
        return int(min_quantity.value)

    def get_max_stock(self):
        """Lấy giá trị số lượng tồn kho tối đa từ cơ sở dữ liệu."""
        max_stock = Regulation.query.filter_by(
            name='Số lượng tồn tối đa',
            is_active=True
        ).first()
        return int(max_stock.value) if max_stock else 300  # Giá trị mặc định là 300


    def get_integer_form_value(self, field_name, default_value=None):
        """Lấy giá trị int từ form và trả về giá trị mặc định nếu không hợp lệ."""
        value = request.form.get(field_name)
        try:
            return int(value) if value else default_value
        except (ValueError, TypeError):
            return default_value

    def get_float_form_value(self, field_name, default_value=None):
        """Lấy giá trị float từ form và trả về giá trị mặc định nếu không hợp lệ."""
        value = request.form.get(field_name)
        try:
            return float(value) if value else default_value
        except (ValueError, TypeError):
            return default_value

    def get_date_form_value(self, field_name, default_value=None):
        """Lấy giá trị ngày từ form và trả về giá trị mặc định nếu không hợp lệ."""
        value = request.form.get(field_name)
        try:
            return datetime.strptime(value, '%Y-%m-%d') if value else default_value
        except (ValueError, TypeError):
            return default_value or datetime.now()

    def create_import_entry(self, book_name, quantity, unit_price, import_date):
        try:
            # Kiểm tra nếu book_name không phải là None
            if not book_name:
                raise ValueError("Tên sách không thể rỗng")

            # Thêm dữ liệu vào bảng import_entries
            import_entry = ImportEntry(
                book_name=book_name,
                quantity=quantity,
                unit_price=unit_price,
                import_date=import_date
            )
            db.session.add(import_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Hoàn tác nếu có lỗi
            flash(f'Đã xảy ra lỗi khi tạo phiếu nhập: {str(e)}', 'error')


class RegulationView(BaseView):
    @expose('/')
    def index(self):
        # Lấy danh sách quy định hiện tại
        regulations = Regulation.query.all()
        return self.render('admin/regulation.html', regulations=regulations)

    @expose('/edit/<int:id>', methods=['GET'])
    def edit_form(self, id):
        # Lấy quy định từ cơ sở dữ liệu
        regulation = Regulation.query.get(id)
        if regulation:
            return self.render('admin/regulation.html', regulation=regulation, regulations=Regulation.query.all())
        else:
            flash('Quy định không tồn tại', 'error')
            return redirect(url_for('.index'))

    @expose('/edit', methods=['POST'])
    def edit_regulation(self):
        regulation_id = request.form.get('id')
        name = request.form.get('name')
        value = request.form.get('value')
        is_active = request.form.get('is_active') == 'on'

        # Kiểm tra xem name và value có hợp lệ không
        if not name or not value:
            flash('Tên và giá trị không thể để trống!', 'error')
            return redirect(url_for('.index'))

        regulation = Regulation.query.get(regulation_id)
        if regulation:
            regulation.name = name
            regulation.value = value
            regulation.is_active = is_active
            db.session.commit()
            flash('Cập nhật quy định thành công!', 'success')
        else:
            flash('Quy định không tồn tại', 'error')

        return redirect(url_for('.index'))

    @expose('/delete/<int:id>', methods=['POST'])
    def delete(self, id):
        regulation = Regulation.query.get(id)
        if regulation:
            db.session.delete(regulation)
            db.session.commit()
            flash('Quy định đã được xóa thành công.', 'success')
        else:
            flash('Không tìm thấy quy định.', 'error')
        return redirect(url_for('.index'))

    @expose('/add', methods=['POST'])
    def add_regulation(self):
        # Lấy dữ liệu từ form
        name = request.form.get('name')
        value = request.form.get('value')
        is_active = request.form.get('is_active') == 'on'

        # Kiểm tra xem tên và giá trị có hợp lệ không
        if not name or not value:
            flash('Tên và giá trị không thể để trống!', 'error')
            return redirect(url_for('.index'))

        # Tạo quy định mới
        new_regulation = Regulation(name=name, value=value, is_active=is_active)
        db.session.add(new_regulation)
        db.session.commit()

        flash('Thêm quy định thành công!', 'success')
        return redirect(url_for('.index'))




admin.add_view(BookCategoryView(BookCategory, db.session))
admin.add_view(BookView(Book, db.session))
admin.add_view(BookImportView(name='Lập Phiếu Nhập Sách', endpoint='bookimportview'))
admin.add_view(RegulationView(name='Thay Đổi Quy Định', endpoint='regulationview'))
admin.add_view(LogoutView(name='Log out'))
