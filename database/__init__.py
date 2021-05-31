from flask_sqlalchemy import SQLAlchemy
import redis #lib to save cache

db = SQLAlchemy() #truy van database
#sqlalchemy là thư viện để viết câu truy vấn database bắng python
#postgres là database , không phải là cơ sở dữ  liệu
#database sinh ra là để lưu trữ cơ sở dữ liệu

#redisdb = redis.StrictRedis(host='localhost', port=6379, db=5) #save session


def init_database(app):  #khoi tao database
    db.init_app(app)