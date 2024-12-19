from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from flask_login import LoginManager
from urllib.parse import quote


app = Flask("__name__")
app.secret_key = '^&*)%T*O&T*^&%)*^T%*&T)*O&RTO)(*FGKYTDFHKTFGK'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/bookstoredb?charset=utf8mb4" % quote ('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)

cloudinary.config(
    cloud_name = 'djbi959vf',
    api_key =  '773466584879955',
    api_secret =  'N-dr2IIPhCScs9UXgtsPNoDE9_g',
)

login = LoginManager(app=app)

