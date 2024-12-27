from datetime import datetime
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from bookapp import db, app
from bookapp.models import BookCategory, Book, UserRole, Regulation, ImportEntry, RegulationImport
from flask_admin import BaseView, expose
from flask_login import current_user, logout_user
from flask import redirect, flash, url_for, request, render_template
import utils


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class BookView(AuthenticatedModelView):
    column_filters = ['name','price']
    column_searchable_list = ['name','author']

    column_list = ['name', 'author', 'description', 'price', 'image', 'active', 'created_date', 'stock', 'category']
    form_columns = ['name', 'author', 'description', 'price', 'image', 'active', 'created_date', 'category_id']
    column_labels = {
        'name': 'Tên sách',
        'author': 'Tác giả',
        'description': 'Mô tả',
        'price': 'Đơn giá',
        'image': 'Hình ảnh',
        'active': 'Trạng thái',
        'created_date': 'Ngày tạo',
        'stock': 'Tồn kho',
        'category': 'Danh mục'
    }


class BookCategoryView(AuthenticatedModelView):
    column_list = ['name']
    form_columns = ['name']
    column_labels = {
        'name': 'Tên danh mục sách',
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
        books = Book.query.all()
        regulations = Regulation.query.filter_by(is_active=True).all()
        return self.render('admin/book_import.html', books=books, regulations=regulations)

    @expose('/add', methods=['POST'])
    def add_import(self):
        try:
            # Lấy thông tin form nhập sách
            book_name = request.form.get('book_name')
            category_name = request.form.get('category_name')
            quantity = self.get_integer_form_value('quantity')
            unit_price = self.get_float_form_value('unit_price')
            import_date = self.get_date_form_value('import_date')

            # Kiểm tra thông tin nhập vào
            if not book_name or not category_name or quantity is None or unit_price is None:
                flash('Vui lòng điền đầy đủ thông tin!', 'error')
                return redirect(url_for('.index'))

            active_regulations = Regulation.query.filter_by(is_active=True).all()
            max_stock_regulation = None
            min_import_regulation = None

            # Tìm các quy định về số lượng tồn tối đa và số lượng nhập tối thiểu
            for regulation in active_regulations:
                if regulation.name == "Số lượng tồn tối đa":
                    max_stock_regulation = regulation
                elif regulation.name == "Số lượng nhập tối thiểu":
                    min_import_regulation = regulation

            # Kiểm tra số lượng nhập tối thiểu
            if min_import_regulation and quantity < float(min_import_regulation.value):
                flash(f'Số lượng nhập phải lớn hơn hoặc bằng {min_import_regulation.value}!', 'error')
                return redirect(url_for('.index'))

            # Kiểm tra số lượng tồn tối đa
            current_book = Book.query.filter_by(name=book_name).first()
            current_stock = current_book.stock if current_book else 0

            if max_stock_regulation:
                max_allowed = float(max_stock_regulation.value)
                if (current_stock + quantity) > max_allowed:
                    allowed_import = max_allowed - current_stock
                    if allowed_import <= 0:
                        flash(f'Không thể nhập thêm sách vì đã đạt số lượng tồn tối đa ({max_allowed})!', 'error')
                    else:
                        flash(f'Số lượng nhập vượt quá quy định! Bạn chỉ được phép nhập thêm {allowed_import} cuốn.', 'error')
                    return redirect(url_for('.index'))

            # Xử lý thêm sách
            category = BookCategory.query.filter_by(name=category_name).first()
            if not category:
                category = BookCategory(name=category_name)
                db.session.add(category)
                db.session.commit()

            if current_book:
                current_book.stock += quantity
                flash(f'Cập nhật số lượng sách "{book_name}" thành công!', 'success')
            else:
                current_book = Book(
                    name=book_name,
                    author=None,
                    description=None,
                    price=unit_price,
                    stock=quantity,
                    category_id=category.id,
                    created_date=import_date
                )
                db.session.add(current_book)
                flash(f'Tạo mới sách "{book_name}" thành công!', 'success')

            db.session.flush()
            import_entry = ImportEntry(
                book_id=current_book.id,
                book_name=book_name,
                quantity=quantity,
                unit_price=unit_price,
                import_date=import_date
            )
            db.session.add(import_entry)
            db.session.flush()

            for regulation in active_regulations:
                reg_import = RegulationImport(
                    regulation_id=regulation.id,
                    import_entry_id=import_entry.id,
                    applied_value=regulation.value
                )
                db.session.add(reg_import)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f'Đã xảy ra lỗi: {str(e)}', 'error')

        return redirect(url_for('.index'))

    def get_integer_form_value(self, field_name, default_value=None):
        value = request.form.get(field_name)
        try:
            return int(value) if value else default_value
        except (ValueError, TypeError):
            return default_value

    def get_float_form_value(self, field_name, default_value=None):
        value = request.form.get(field_name)
        try:
            return float(value) if value else default_value
        except (ValueError, TypeError):
            return default_value

    def get_date_form_value(self, field_name, default_value=None):
        value = request.form.get(field_name)
        try:
            return datetime.strptime(value, '%Y-%m-%d') if value else default_value
        except (ValueError, TypeError):
            return default_value or datetime.now()

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role in [UserRole.ADMIN, UserRole.QLKHO]


class RegulationView(BaseView):
    @expose('/')
    def index(self):
        regulations = Regulation.query.all()
        import_entries = ImportEntry.query.all()
        return self.render('admin/regulation.html',
                         regulations=regulations,
                         import_entries=import_entries)

    @expose('/edit/<int:id>', methods=['GET'])
    def edit_form(self, id):
        regulation = Regulation.query.get(id)
        if regulation:
            return self.render('admin/regulation.html',
                             regulation=regulation,
                             regulations=Regulation.query.all(),
                             import_entries=ImportEntry.query.all())
        else:
            flash('Quy định không tồn tại', 'error')
            return redirect(url_for('.index'))

    @expose('/edit', methods=['POST'])
    def edit_regulation(self):
        try:
            regulation_id = request.form.get('id')
            name = request.form.get('name')
            value = request.form.get('value')
            is_active = request.form.get('is_active') == 'on'

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

        except Exception as e:
            db.session.rollback()
            flash(f'Đã xảy ra lỗi: {str(e)}', 'error')

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
        try:
            name = request.form.get('name')
            value = request.form.get('value')
            is_active = request.form.get('is_active') == 'on'

            if not name or not value:
                flash('Tên và giá trị không thể để trống!', 'error')
                return redirect(url_for('.index'))

            new_regulation = Regulation(name=name, value=value, is_active=is_active)
            db.session.add(new_regulation)
            db.session.commit()

            flash('Thêm quy định thành công!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Đã xảy ra lỗi: {str(e)}', 'error')

        return redirect(url_for('.index'))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role in [UserRole.ADMIN, UserRole.QLKHO]


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return render_template('admin/login.html')
        return super(MyAdminIndexView, self).index()


class StatsView(BaseView):
    @expose('/')
    def index(self):
        current_date = datetime.now()
        year = request.args.get('year', current_date.year, type=int)
        month = request.args.get('month', current_date.month, type=int)

        revenue_stats = utils.stats_by_category(month, year)
        book_stats = utils.stats_book_sold(month, year)

        total_revenue = sum(stat[1] for stat in revenue_stats) if revenue_stats else 0

        years = range(2020, current_date.year + 1)

        return self.render('admin/stats.html',
                         year=year,
                         month=month,
                         years=years,
                         revenue_stats=revenue_stats,
                         book_stats=book_stats,
                         total_revenue=total_revenue)
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role in [UserRole.ADMIN, UserRole.QLKHO]

# Khởi tạo Admin với view tùy chỉnh
admin = Admin(app=app,
             name="BookStore Management",
             template_mode="bootstrap4",
             index_view=MyAdminIndexView())

# Thêm các view vào admin
admin.add_view(BookCategoryView(BookCategory, db.session, name='Danh mục sách'))
admin.add_view(BookView(Book, db.session, name='Sách'))
admin.add_view(BookImportView(name='Lập Phiếu Nhập Sách', endpoint='bookimportview'))
admin.add_view(RegulationView(name='Thay Đổi Quy Định', endpoint='regulationview'))
admin.add_view(StatsView(name='Thống Kê - Báo Cáo', endpoint='statsview'))
admin.add_view(LogoutView(name='Đăng xuất'))