from application.database import db
from application import app
from flask import render_template,json, request, url_for, jsonify
from application.controller.helper_common_api import current_uid
from application.model.model import User, Role, roles_users, BenhNhan
from sqlalchemy import and_, or_, desc, asc
from application.controller.helper_common_api import decrypt_password, response_current_user, encrypt_password, to_dict, convert_text_khongdau
import hashlib
import math
from math import ceil
from application.controller.helper_common_api import encrypt_password, generator_salt,default_uuid
from datetime import datetime


@app.route("/") #"/" = route
def begin():
    return render_template('index.html') #index.html = file load html dau tien

#khi lam viec(truyen du lieu, nhan du lieu) nguoi ta su dung chuoi json
#chuoi json duoc bien doi tu kieu du lieu thong thuong
# so, chuoi, object, mang
#khi nhan duoc chuoi json, muon su dung thi bien no ve kieu du lieu thong thuong
@app.route("/api/v1/current_user")
#def check_current_user():
    # return json.dumps(data), 200
#    return json.dumps({"error_code": "SESSION_EXPIRED", "error_msg": "Hết phiên làm việc, vui lòng đăng nhập lại!"}),520
#method cho phep phuong thuc goi den API
#post : gui du lieu len(thuong de truyen)
#get(thuong de lay du lieu tren thanh dia chi): truyen du lieu tren thanh dia chi(co gioi han) va khong duoc bao mat
#put : update du lieu

@app.route("/api/v1/register", methods = ["POST", 'GET'])#4 methods: post, get, put, delete
def register():
    data = request.json #lay du lieu json gui kem request 
    if data is None:
        return json.dumps({"error_code" : "PARAM_ERROR", "error_message": "Tham số không hợp lệ"}), 520
    hoten = data.get("hoten", None) #dict object: key -value
    phone = data.get("phone", None)
    email = data.get("email", None)
    password = data.get("password", None)
    confirm_password = data.get("password_confirm", None)
    if email is None and phone is None:
        #jsonify=json.dumps: chuyen object-> json
        return jsonify({"error_code": "PARAM_ERROR", "error_message" : "Vui lòng nhập số điện thoại hoặc email"}),520
    if password != confirm_password:
        return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Mật khẩu không khớp vui lòng thử lại'}),520

    #check so dien thoai
    if phone is not None and phone != "":
        checkUser = db.session.query(User).filter(and_(User.dienthoai == phone)).first()
        #giao tiep voi database = query, 1 query tao ra 1 session
        #filter co the co nhieu dieu kien
        #first = lay ban ghi dau tien
        if checkUser is not None:
            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Số điện thoại đã có người đăng ký.'}),520
    
    #check email
    if email is not None and email  != "":
        checkUser = db.session.query(User).filter(User.email == email).first()
        if checkUser is not None:
            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Email đã có người đăng ký.'}),520


    newUser = User()#khoi tao 1 User
    newUser.id = default_uuid()
    newUser.hoten = hoten
    newUser.dienthoai = phone
    newUser.email = email
    salt = str(generator_salt()) #key encoder passwords
    newUser.salt = salt
    newUser.matkhau = encrypt_password(password, salt)
    newUser.active =1 
    role_user = db.session.query(Role).filter(Role.vaitro == 'user').first()
    listRole = []
    if role_user is not None:
        listRole.append((role_user))
        newUser.vaitro = listRole
    db.session.add(newUser)
    db.session.commit()  #luu vao database Postgres

    return jsonify(to_dict(newUser)),200


@app.route("/api/v1/login", methods = ["POST"])
def login():
    data = request.json
    if data is None:
        return json.dumps({"error_code" : "PARAM_ERROR", "error_message": "Tham số không hợp lệ"}), 520
    taiKhoan = data.get("data")
    matKhau = data.get("password")
    if taiKhoan is None or matKhau is None:
        return json.dumps({"error_code" : "PARAM_ERROR", "error_message" : "Than số không hợp lệ"}), 520
    #check          
    check_user = db.session.query(User).filter(and_(or_(User.taikhoan == taiKhoan, \
        User.email == taiKhoan, User.dienthoai == taiKhoan), User.active == 1)).first()
    if check_user is not None:
        salt = check_user.salt
        password = decrypt_password(check_user.matkhau, salt)
        if password == matKhau:
            return json.dumps(response_current_user(check_user)),200
        else:
            return json.dumps({"error_code":"LOGIN_FAILED", "error_message":u"Mật khẩu không đúng"}),520
    else:    
        return json.dumps({"error_code":"LOGIN_FAILED", "error_message":u"Tài khoản không tồn tại"}),520


@app.route('/logout', methods=['GET'])    
def logout():
    return json.dumps({"error_message": "successful!"}),200

@app.route('/api/v1/user', methods = ['GET'])
def getUser():
    page = int(request.args.get('page'))
    results_per_page = int(request.args.get('results_per_page'))
    ## phân trang de gioi han moi lan lay du lieu
    if page is None:
        page = 1
    if results_per_page is None:
        results_per_page = 10
    elif results_per_page == 0:
        results_per_page = 1
    ##đếm số bản ghi trong database 
    countUser = db.session.query(User).filter(User.active == 1).count()
    ##Tổng số trang
    total_pages = math.ceil(countUser/results_per_page)  #lam tron
    num_results = 0
    listResult = []
    listUser = db.session.query(User).filter(User.active==1)

    listUser = listUser.limit(results_per_page).offset(results_per_page*(page-1)).all()
    #offset = bo qua

    if isinstance(listUser, list):
        for item in listUser:
            tmp = to_dict(item)
            tmp['stt'] = num_results + 1
            del tmp['salt']
            del tmp['matkhau']
            listResult.append(tmp)
            num_results+=1


    return json.dumps({'page' : page,'objects' : listResult,'total_pages': total_pages,'num_results': num_results}),200


@app.route('/api/v1/user', methods = ['POST'])
#only for admin to create new User
def postUser():
    data = request.json
    if data is None:
        return json.dumps({"error_code" : "PARAM_ERROR", "error_message" : "Tham số không hợp lệ"}), 520
    #check so dien thoai
    phone = data['dienthoai']
    if phone is not None and phone != "":
        checkUser = db.session.query(User).filter(and_(User.dienthoai == phone)).first()
        if checkUser is not None:
            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Số điện thoại đã tồn tại trong hệ thống.'}),520
    #check email
    email = data['email']
    if email is not None and email  != "":
        checkUser = db.session.query(User).filter(User.email == email).first()
        if checkUser is not None:
            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Email đã tồn tại trong hệ thống.'}),520
    #check tai khoan
    taikhoan = data['taikhoan']
    if taikhoan is not None and taikhoan != "":
        checkUser = db.session.query(User).filter(and_(User.taikhoan == taikhoan)).first()
        if checkUser is not None:
            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Tài khoản đã tồn tại trong hệ thống'}),520


    newUser = User()
    newUser.id = default_uuid()
    newUser.hoten = data['hoten']
    newUser.tenkhongdau = convert_text_khongdau(data['hoten'])
    newUser.ngaysinh = data['ngaysinh']
    newUser.chungminhnhandan = data['chungminhnhandan']
    newUser.noilamviec = data['noilamviec']
    newUser.email = data['email']
    newUser.dienthoai = data['dienthoai']
    newUser.taikhoan = data['taikhoan']
    salt = str(generator_salt())
    newUser.salt = salt
    newUser.matkhau = encrypt_password(data['matkhau'], salt)
    newUser.active = 1
    role_user = db.session.query(Role).filter(Role.vaitro == 'user').first()
    listRole = []
    if role_user is not None:
        listRole.append((role_user))
        newUser.vaitro = listRole
    db.session.add(newUser)
    db.session.commit()

    return json.dumps({'error_code' : 'Successfull', 'error_message': 'Lưu thông tin thành công'}),200

@app.route('/api/v1/user/<id>', methods = ['GET', 'PUT'])
def getUserByID(id):
    if id is None:
        return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : "Tham số không hợp lệ"}), 520
    else:
        if request.method == "GET":
            checkUser = db.session.query(User).filter(User.id == id).first()
            #lay user co id = id truyen len
            if checkUser is None:
                return json.dumps({'error_code' : 'PARAM_NOT_EXIST', 'error_message' : 'Không tìm thấy bản ghi dữ liệu'}),520
            else:
                tmp = to_dict(checkUser)
                del tmp['matkhau']
                return jsonify(tmp),200
        elif request.method == "PUT":
            data = request.json
            if data is None:
                return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Tham số không hợp lệ'}),520
            if 'id' in data and data['id'] is not None:
                checkUser = db.session.query(User).filter(User.id == data['id']).first()
                if checkUser is None:
                    return json.dumps({'error_code': 'PARAM_NOT_EXIST', 'error_message' : 'Không tìm thấy bản ghi dữ liệu'}),520
                else:
                    checkUser.hoten = data['hoten']
                    checkUser.tenkhongdau = convert_text_khongdau(data['hoten'])
                    checkUser.ngaysinh = data['ngaysinh']
                    checkUser.chungminhnhandan = data['chungminhnhandan']
                    checkUser.noilamviec = data['noilamviec']
                    #check so dien thoai
                    phone = data['dienthoai']
                    if phone is not None and phone != "":
                        checkUser1 = db.session.query(User).filter(and_(User.dienthoai == phone, User.id != data['id'])).first()
                        if checkUser1 is not None:
                            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Số điện thoại đã tồn tại trong hệ thống.'}),520
                    #check email
                    email = data['email']
                    if email is not None and email  != "":
                        checkUser1 = db.session.query(User).filter(User.email == email, User.id != data['id']).first()
                        if checkUser1 is not None:
                            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Email đã tồn tại trong hệ thống.'}),520
                    #check tai khoan
                    taikhoan = data['taikhoan']
                    if taikhoan is not None and taikhoan != "":
                        checkUser1 = db.session.query(User).filter(and_(User.taikhoan == taikhoan, User.id != data['id'])).first()
                        if checkUser1 is not None:
                            return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Tài khoản đã tồn tại trong hệ thống'}),520

                    checkUser.email = data['email']
                    checkUser.dienthoai = data['dienthoai']
                    checkUser.taikhoan = data['taikhoan']
                    checkUser.active = 1
                    if data['matkhau'] is not None and data['matkhau'] != "":
                        if checkUser.salt is not None:
                            newMatKhau = encrypt_password(data['matkhau'], checkUser.salt)
                            checkUser.matKhau = newMatKhau
                        else:
                            salt = str(generator_salt())
                            newMatKhau = encrypt_password(data['matkhau'], salt)
                            checkUser.matKhau = newMatKhau
                    
                    db.session.commit()
                    return jsonify(to_dict(checkUser)),200
            else:
                return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Tham số không hợp lệ'}),520


@app.route('/api/v1/benhnhan', methods = ['GET'])
def getBenhNhan():
    page = int(request.args.get('page')) #args to get any bien tren URL
    results_per_page = int(request.args.get('results_per_page'))
    filters = request.args.get("q")
    if filters is not None:
        filters = json.loads(filters) #json.loads -> convert to the original dtype
        #{'hoten': {'like':'keyword search'}}
        #{'tenkhongdau': {'like':'keyword search'}}
    arr = []
    keys1 = ""
    keys2 = ""
    #doan duoi de lay key words searching: key1(ko dau), key2(co dau-original)

    if isinstance(filters, dict) and "filters" in filters and filters['filters'] is not None:
        obj = filters['filters']
        if '$or' in obj and obj['$or'] is not None:
            arr = obj['$or']
            if isinstance(arr, list) and len(arr) >0:
                dataSearch1 = arr[0]
                if 'tenkhongdau' in dataSearch1 and dataSearch1['tenkhongdau'] is not None:
                    keys1 = dataSearch1['tenkhongdau']['$likeI']
                dataSearch2 = arr[1]
                if 'hoten' in dataSearch2 and dataSearch2['hoten'] is not None:
                    keys2 = dataSearch2['hoten']['$likeI']
                

    ## phân trang
    if page is None:
        page = 1
    if results_per_page is None:
        results_per_page = 10
    elif results_per_page == 0:
        results_per_page = 1
    ##đếm số bản ghi trong database 
    countBenhNhan = db.session.query(BenhNhan).count()
    ##Tổng số trang
    total_pages = math.ceil(countBenhNhan/results_per_page)
    num_results = 0
    listResult = []
    listBenhNhan = db.session.query(BenhNhan)

    #search
    if (keys1 is not None and keys1 != "") or (keys2 is not None and keys2 != ""):
        text2 = '%{}%'.format(keys2)
        text1 = '%{}%'.format(keys1)
        listBenhNhan = listBenhNhan.filter(or_(BenhNhan.hoten.like(text2), BenhNhan.tenkhongdau.ilike(text1)))
        #ilike = bo qua viet hoa viet thuong, like = phan biet hoa thuong


    listBenhNhan = listBenhNhan.limit(results_per_page).offset(results_per_page*(page-1)).all()

    if isinstance(listBenhNhan, list):
        for item in listBenhNhan:
            tmp = to_dict(item)
            tmp['stt'] = num_results+1
            listResult.append(tmp)
            num_results+=1


    return json.dumps({'page' : page,'objects' : listResult,'total_pages': total_pages,'num_results': num_results}),200

@app.route('/api/v1/benhnhan', methods = ['POST'])
#tao benh nhan
def postBenhNhan():
    data = request.json
    if data is None:
        return json.dumps({"error_code" : "PARAM_ERROR", "error_message" : "Tham số không hợp lệ"}), 520
    hoTen = data.get("hoten")
    if hoTen is None or hoTen == "":
        return jsonify({'error_code': 'PARAM_ERROR', 'error_message': 'Tham số không hợp lệ'}),520
    benhNhan = BenhNhan()
    benhNhan.id = default_uuid()
    benhNhan.hoten = hoTen
    benhNhan.tenkhongdau = convert_text_khongdau(hoTen)
    benhNhan.ngaysinh = data.get("ngaysinh", None)
    benhNhan.gioitinh = data.get("gioitinh", None)
    
    benhan = data.get("benhan")
    if benhan is not None:
        benhNhan.benhan = benhan
        now = datetime.now().timestamp()
        benhNhan.updated_at = now
        uid = data.get("uid")
        if uid is not None:
            benhNhan.created_by = uid
    db.session.add(benhNhan)
    db.session.commit()

    return jsonify(to_dict(benhNhan)),200

@app.route('/api/v1/benhnhan/<id>', methods = ['GET', 'PUT','DELETE'])
#get or update patient informations by id
def get_put_BenhNhan(id):
    if id is None:
        return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : "Tham số không hợp lệ"}), 520
    else:
        if request.method == "GET":
            #database -> session -> query
            checkBenhNhan = db.session.query(BenhNhan).filter(BenhNhan.id == id).first()
            # =object of SQLachemy
            if checkBenhNhan is None:
                return json.dumps({'error_code' : 'PARAM_NOT_EXIST', 'error_message' : 'Không tìm thấy bản ghi dữ liệu'}),520
            else:
                tmp = to_dict(checkBenhNhan)
                return jsonify(tmp),200
        elif request.method == "PUT":
            data = request.json
            if data is None:
                return json.dumps({'error_code' : 'PARAM_ERROR', 'error_message' : 'Tham số không hợp lệ'}),520       

            checkBenhNhan = db.session.query(BenhNhan).filter(BenhNhan.id == id).first()
            if checkBenhNhan is None:
                return jsonify({'error_code' : 'PARAM_NOT_EXIST', 'error_message' : 'Không tìm thấy bản ghi dữ liệu'}),520
            else:
                hoTen = data.get("hoten")
                if hoTen is None or hoTen == "":
                    return jsonify({'error_code' : 'PARAM_ERROR', 'error_message' : 'Tham số không hợp lệ'}),520

                checkBenhNhan.hoten = hoTen
                checkBenhNhan.tenkhongdau = convert_text_khongdau(hoTen)
                checkBenhNhan.ngaysinh = data.get("ngaysinh", None)  #khong bao loi khi khong co key
                checkBenhNhan.gioitinh = data.get("gioitinh", None)
                    
                benhan = data.get("benhan")
                if benhan is not None:
                    now = datetime.now().timestamp()
                    checkBenhNhan.benhan = benhan
                    checkBenhNhan.updated_at = now
                    uid = data.get("uid")
                    if uid is not None and uid != "":
                        checkBenhNhan.created_by = uid
                db.session.commit()

                return jsonify(to_dict(checkBenhNhan)),200

        elif request.method == "DELETE":
            checkBenhNhan = db.session.query(BenhNhan).filter(BenhNhan.id == id).first()
            if checkBenhNhan is None:
                return jsonify({'error_code' : 'PARAM_NOT_EXIST', 'error_message' : 'Không tìm thấy bản ghi dữ liệu'}),520
            else:
                checkBenhNhan = db.session.query(BenhNhan).filter(BenhNhan.id == id).delete()
                db.session.commit()
                return jsonify({'error_code' : 'succesful', 'error_message': 'Xóa dữ liệu thành công'}),200