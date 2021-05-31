import os, sys
import io
from PIL import Image
import time
import os.path
import httplib2
import base64
import ujson
import requests
import random,string
from werkzeug.utils import secure_filename

from flask import render_template,json, request, url_for, jsonify
# from gatco import Blueprint
from application import app
from application.database import db
from application.controller.helper_common_api import to_dict


import aiofiles
import hashlib
from application.model.model import FileInfo
from application.model.model import User
import uuid
from application.controller.helper_common_api import default_uuid



def allowed_file(filename):
    # return '.' in filename and \
    #        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True

@app.route('/api/v1/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['FS_ROOT'], filename))
            # return redirect(url_for('uploaded_file',
            #                         filename=filename))
            fileInfo = FileInfo()
            fileInfo.id = default_uuid()
            fileInfo.name = filename
            fileInfo.link = app.config['DOMAIN_URL'] + '/static/file/uploads/' + filename
            db.session.add(fileInfo)
            db.session.commit()
            return jsonify(to_dict(fileInfo)),200
    
    return json.dumps({"error_code" : 'PARAM_ERROR', 'error_message' : 'Tải file không thành công'}),520
