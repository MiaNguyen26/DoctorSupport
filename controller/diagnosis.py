import numpy as np
import tensorflow as tf
import keras 
from keras.layers import *
from keras.models import Model
from keras.optimizers import *
from keras.layers.normalization import BatchNormalization
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint
import cv2 as cv 
from keras.initializers import RandomNormal
from keras.layers import Activation
import os
import os.path
#import sys
#import random
from glob import glob
# import matplotlib.pyplot as plt
#from skimage.io import imread
#from skimage import io
from keras import backend as K
from application import app
from flask import render_template,json, request, url_for, jsonify
import time
from datetime import datetime
from application.controller.helper_common_api import default_uuid, to_dict
from application.model.model import FileInfo
from application.database import db






@app.route('/test_image', methods = ['GET'])
def test():
    TARGET = 256
    # tf.keras.preprocessing.image.load_img
    #img1 = tf.keras.preprocessing.image.load_img("/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/N22-Benh_an_xa_Phuong.jpg")
    #print(a)
    
    #b = tf.keras.utils.get_file("b", "https://drive.google.com/file/d/1-M-o6TRN3pAT0--49PYBP7mF4m93GFaL/view?usp=sharing", untar=True)
    
    img1 = tf.keras.preprocessing.image.load_img('/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/ID00015637202177877247924_124.jpg', color_mode="grayscale", target_size=(TARGET, TARGET))
    img1 = tf.keras.preprocessing.image.img_to_array(img1)
    img1 = img1[:,:,0]  #array: 512x512
    img1 = img1.reshape(TARGET, TARGET, 1)  
#print(np.unique(img1))  
    img = img1/255.
    #print(img.shape)
    img = np.array(img).reshape((1, TARGET, TARGET,1))
    #img = np.reshape(img, (1, TARGET, TARGET, 1))
    #print(img.shape)
    unet_model = tf.keras.models.load_model("/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/IMGPre_G30804_12eps_BS2_size256_Dice_tracheaSEG_1105.h5", custom_objects= {'dice_coef_loss':dice_coef_loss, 'dice_coef_n':dice_coef_n} )
    predict = unet_model.predict(img)
    gray = 255*predict
    print("x=suuu============================================: ", gray.shape)
    gray = np.asmatrix(gray)
    print("xxxxxxxxxxxxxxxxxxx===========================: ", gray.shape)
    #gray1 = np.array(gray)
    #gray1 = np.reshape(gray1, (TARGET, TARGET, 3))
    #print("xxxsjanjccnnnnnnnnnnnnnnnn:", gray1.shape)
    cv.imwrite('/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/a.jpg',gray)
    #gray = 255*gray
    #save_path = '/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/'
    #name_of_file = 'ABC'
    # file.save(os.path.join(app.config['FS_ROOT'], filename))

    #gray1.save(os.path.join(save_path, name_of_file+".png"))
    
    #tf.keras.preprocessing.image.save_img('/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/', gray1)
    return jsonify({}),200

def dice_coef_n(y_true, y_pred, smooth=1.0):
    '''Average dice coefficient per batch.'''
    axes = (1,2,3)
    intersection = K.sum(y_true * y_pred, axis=axes)
    summation = K.sum(y_true + y_pred, axis=axes)
    
    return K.mean((2.0 * intersection + smooth) / (summation + smooth), axis=0)
    
def dice_coef_loss(y_true, y_pred):
    return 1.0 -dice_coef_n(y_true, y_pred)


@app.route("/api/v1/chandoan_hinhanh", methods = ['POST'])
def chandoan_hinhanh():
    data = request.json
    if data is None:
        return jsonify({'error_code': 'PARAM_ERROR', 'error_message': "Tham số không hợp lệ"}),520
    
    arr = []
    # list_hinhanh = data.get("parmas")
    list_hinhanh = data
    if list_hinhanh is None:
        list_hinhanh = []
    TARGET = 256
    for item in list_hinhanh:
        name = item['name']
        url_image = app.config.get("FS_ROOT", "/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/") + name
        img = tf.keras.preprocessing.image.load_img(url_image, color_mode="grayscale", target_size=(TARGET, TARGET))
        img = tf.keras.preprocessing.image.img_to_array(img)
        img = img[:,:,0]  #array: 512x512
        img = img.reshape(TARGET, TARGET, 1)
        
        img_tmp = img/255
        img_tmp = np.array(img_tmp).reshape((1, TARGET, TARGET,1))
        unet_model = tf.keras.models.load_model("/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/IMGPre_G30804_12eps_BS2_size256_Dice_tracheaSEG_1105.h5", custom_objects= {'dice_coef_loss':dice_coef_loss, 'dice_coef_n':dice_coef_n} )

        # unet_model = tf.keras.models.load_model("/home/duy/Documents/workspace/chandoanbenh/repo/application/static/file/uploads/IMGPre_G30804_12eps_BS2_size256_Dice_tracheaSEG_1105.h5", custom_objects= {'dice_coef_loss':dice_coef_loss, 'dice_coef_n':dice_coef_n} )
        predict = unet_model.predict(img_tmp)
        gray = 255*predict
        gray = np.asmatrix(gray)
        name_image =  str((time.time())) + name
        path = "/home/mianguyen/workspace/chandoanbenh/repo/application/static/file/uploads/"
        url = path + name_image
        cv.imwrite(url,gray)

        fileInfo = FileInfo()
        fileInfo.id = default_uuid()
        fileInfo.name = name_image
        fileInfo.link = app.config['DOMAIN_URL'] + '/static/file/uploads/' + name_image
        db.session.add(fileInfo)
        arr.append(to_dict(fileInfo))
        db.session.flush()

    db.session.commit()

    return jsonify({'results' : arr}),200

