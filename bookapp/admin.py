from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from bookapp import db, app
from bookapp.models import BookCategory, Book, UserRole
from flask_admin import BaseView, expose
from flask_login import current_user, logout_user, login_required
from flask import redirect


admin = Admin(app=app, name="BookStore Management", template_mode="bootstrap4")


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class BookView(AuthenticatedModelView):
    # Kiểm tra lại các trường trong form_columns dưới dạng list
    column_list = ['name', 'author', 'description', 'price', 'image', 'active', 'created_date', 'category']  # Hiển thị tên category
    form_columns = ['name', 'author', 'description', 'price', 'image', 'active', 'created_date', 'category_id']  # Người dùng chọn category
    column_labels = {
        'name': 'Book Name',
        'author': 'Author',
        'description': 'Description',
        'price': 'Price',
        'image': 'Image',
        'active': 'Active',
        'created_date': 'Created Date',
        'category': 'Category'
    }


class BookCategoryView(AuthenticatedModelView):
    column_list = ['name']
    form_columns = ['name']
    column_labels = {
        'name': 'Category Name'
    }


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


admin.add_view(BookCategoryView(BookCategory, db.session))
admin.add_view(BookView(Book, db.session))
admin.add_view(LogoutView(name='Log out'))
