class Config(object):
    DEBUG = True #mode chay project
    STATIC_URL = '/static'  #khai bao duong dan thu muc chua file static = front-end = HTML, CSS, JS
    SQLALCHEMY_DATABASE_URI = 'postgresql://chandoanuser:123243jhsdfsdh@127.0.0.1:5432/chandoan' #duong dan ket noi database 


    DOMAIN_URL = 'http://127.0.0.1:10000' #10000=port=giao tiep
    FS_ROOT= "/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/" #link upload image/file
    FS_ROOT_FILE= "/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/diagnosis/"

