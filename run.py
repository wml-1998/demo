# -*- coding: utf-8 -*-
import paddlehub as hub
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import join
import tensorflow as tf
import cv2
import sys
import time
from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow
from ui.YQ_form import Ui_YQ_form
# import icon_rc
import time
import io
import base64
from aip import AipFace
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QApplication
import socket
import json
import random
from threading import Thread

# 配置百度aip参数
APP_ID = '19484855'
API_KEY = 'V2mDOleCsk3yEE6P5MgVwSjI'
SECRET_KEY = 'RbRMAuPmz8QpDweikrbpfGQjXUm7HiCD'
a_face = AipFace(APP_ID, API_KEY, SECRET_KEY)
image_type = 'BASE64'
options = {'face_field': 'age,gender,beauty', "max_face_num": 10}
max_face_num = 10

AP = 0
NP = 0
UNP = 0


def get_file_content(file_path):
    """获取文件内容"""
    with open(file_path, 'rb') as fr:
        content = base64.b64encode(fr.read())
        return content.decode('utf8')


def face_score(file_path):
    """脸部识别分数"""
    result = a_face.detect(get_file_content(file_path), image_type, options)
    return result

host = "117.78.1.201" #AIOT云平台tcp连接host地址
port = 8700           #AIOT云平台tcp连接port

def socket_client(host,port):
    ''''
    创建TCP连接
    '''
    handshare_data = {
            "t": 1,                                    #固定数据代表连接请求
            "device": "2020010414",                 #设备标识
            "key": "f83f6d22439c4965a52c02bc5dbb41a9", #传输密钥
            "ver": "v1.0"}                             #客户端代码版本号,可以是自己拟定的一组客户端代码版本号值
    try:
        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #创建socket
        tcp_client.connect((host,port))                                #建立tcp连接
        tcp_client.send(json.dumps(handshare_data).encode())           #发送云平台连接请求
        res_msg = tcp_client.recv(1024).decode()                       #接收云平台响应
    except Exception as e:
        print(e)
        return False
    return tcp_client                                                  #返回socket对象

def listen_server(socket_obj):
    '''
    监听TCP连接服务端消息
    :param socket_obj:
    :return:
    '''
    while True:
        try:
            res = socket_obj.recv(1024).decode() #接收服务端数据
            if not res:
                exit()
        except Exception as e:
            print(e)
            exit()

def tcp_ping(socket_obj):
    '''
    TCP连接心跳包
    :param socket_obj:
    :param obj:
    :return:
    '''
    while True:
        try:
            socket_obj.send("$#AT#".encode())   #发送心跳包数据
            time.sleep(30)
        except Exception as e:
            print(e)
            exit()

def send_temperature(tcp_client,num,fever,mask,age,AP,NP,UNP):
    '''

    :param tcp_client: socket对象
    :param num: 体温数据
    :return:
    '''
    if fever == 1:
        AP = AP + 1
        UNP = UNP + 1
        NP = NP + 0
        data = {
            "t": 3,                                      #固定数字,代表数据上报
            "datatype": 1,                               #数据上报格式类型
            "datas":
            {
            "YQ_PTem": num,                      #体温数据
             "YQ_UPTem": num,               #异常体温数据
                "YQ_IfKz": mask,
                 "YQ_age": age,
                  "YQ_IfFever":fever,
                   "YQ_AP": AP,
                    "YQ_NP": NP,
                     "YQ_UNP": UNP,


            },
            "msgid": str(random.randint(100,100000))     #消息编号
        }
    else:
        AP = AP + 1
        NP = NP + 1
        data = {
            "t": 3,
            "datatype": 1,
            "datas":
            {
            "YQ_PTem": num,
             "YQ_IfKz": mask,
              "YQ_age": age,
               "YQ_IfFever": fever,
                "YQ_AP": AP,
                 "YQ_NP": NP,
                  "YQ_UNP": UNP,
            },
            "msgid": str(random.randint(100,100000))
        }
    try:
        tcp_client.send(json.dumps(data).encode())       #发送数据
    except Exception as e:
        print(e)


class CameraPage(QMainWindow,Ui_YQ_form):
    """
     摄像头界面类
     """
    def __init__(self):
        super(CameraPage, self).__init__()
        self.setupUi(self)
        self.showImage = None
        self.num = 0  ##用于计数
        self.camera_btn.clicked.connect(self.camera_btn_clicked)
        self.photo_btn.clicked.connect(self.photo_btn_clicked)
        self.photo_btn_2.clicked.connect(self.photo_btn_2_clicked)
        self.photo_yc.clicked.connect(self.photo_yc_clicked)
        self.photo_sx.clicked.connect(self.photo_sx_clicked)

    def photo_sx_clicked(self):
        strk = ""
        self.text_mask.setText(strk)
        self.textage.setText(strk)
        self.text_temp.setText(strk)
        self.text_fever.setText(strk)
        pixmap = QPixmap("/try/999.jpg")  # 按指定路径找到图片
        self.label_show_photo_2.setPixmap(pixmap)
        # self.label_show_photo_2.delete('1.0', 'end')

    def photo_btn_clicked(self):
       # if self.showImage:
                self.label_show_photo_2.setPixmap(self.showImage)  ##将摄像头获取到的图片展示在label上
                screen = QApplication.primaryScreen()
                pix = screen.grabWindow(self.label_show_camera.winId())
                dir_ = 'C:/Users/LENOVO/Desktop/YQ_demo/new_img.jpg'
                pix.save(dir_)

    def photo_yc_clicked(self):
        test_img_path = ["new_img.jpg"]
        module = hub.Module(name="pyramidbox_lite_server_mask")
        input_dict = {"image": test_img_path}
        results = module.face_detection(data=input_dict)
        str4 = " ".join('%s' % id for id in results)
        print(str4.find('NO MASK'))
        aa = str4.find('NO MASK')
        # 图片地址，图片与程序同一目录下
        file_path = "new_img.jpg"
        result = face_score(file_path)
        # #从文件读取图像并转为灰度图像
        img = cv2.imread(file_path)
        # 图片放文字
        # 设置文件的位置、字体、颜色等参数
        font = cv2.FONT_HERSHEY_DUPLEX
        # font = ImageFont.truetype("simhei.ttf", 20, encoding="utf-8")
        color = (0, 0, 255)
        for item in result['result']['face_list']:
            x = int(item['location']['left'])
            y = int(item['location']['top'])
            w = item['location']['width']
            h = item['location']['height']
            age = item['age']
            beauty = item['beauty']
            gender = item['gender']['type']
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3)
            cv2.putText(img, 'age:%s' % age, (x, y + h + 10), font, 1, color, 1)
            cv2.putText(img, 'beauty:%s' % beauty, (x, y + h + 30), font, 1, color, 1)
            cv2.putText(img, 'gender:%s' % gender, (x, y + h + 50), font, 1, color, 1)
        # cv2.imshow('Image', img)
        # 按任意键退出
        key = cv2.waitKey()
        if key == 27:
            # 销毁所有窗口
            cv2.destroyAllWindows()
        if aa == -1:
            self.text_mask.setText("1")
            str4 = str(age)
            self.textage.setText(str4)
            str5 = self.text_temp.toPlainText();
            str2 = self.textage.toPlainText();
            a = float(str5)
            b = int(str2)
            if b <= 2 and a > 38.0:
                c = 1
            if b <= 2 and a <= 38.0:
                c = 0
            if b >= 3:
                if b <= 10 and a > 37.8:
                    c = 1
            if b >= 3:
                if b <= 10 and a <= 37.8:
                    c = 0
            if b >= 11:
                if b <= 65 and a > 37.5:
                    c = 1
            if b >= 11:
                if b <= 65 and a <= 37.5:
                    c = 0
            if a > 37.4 and b >= 65:
                c = 1
            if a > 37.4 and b >= 65:
                c = 0
            str3 = str(c)
            self.text_fever.setText(str3)
        else:
            self.text_mask.setText("0")
            str4 = str(age)
            self.textage.setText(str4)
            str5 = self.text_temp.toPlainText();
            str2 = self.textage.toPlainText();
            a = float(str5)
            b = int(str2)
            if b <= 2 and a > 38.0:
                c = 1
            if b <= 2 and a <= 38.0:
                c = 0
            if b >= 3:
                if b <= 10 and a > 37.8:
                    c = 1
            if b >= 3:
                if b <= 10 and a <= 37.8:
                    c = 0
            if b >= 11:
                if b <= 65 and a > 37.5:
                    c = 1
            if b >= 11:
                if b <= 65 and a <= 37.5:
                    c = 0
            if a > 37.4 and b >= 65:
                c = 1
            if a > 37.4 and b >= 65:
                c = 0
            str3 = str(c)
            self.text_fever.setText(str3)

    def photo_btn_2_clicked(self):
        strtem = self.text_temp.toPlainText();
        strfever = self.text_fever.toPlainText();
        strmask = self.text_mask.toPlainText();
        strage = self.textage.toPlainText();
        tem = float(strtem)
        fever = int(strfever)
        mask = int(strmask)
        age = int(strage)
        send_temperature(tcp_client,tem,fever,mask,age,AP,NP,UNP)  # 发送一条体温数据


    def camera_btn_clicked(self):
        """
        摄像头按钮点击相应
        功能：打开关闭
        摄像头，并修改对应ui
        :return:
        """
        if self.num == 0:  # 打开摄像头
           self.label_info.setText('摄像头已打开！')  ##label设置文字
           self.camera_btn.setStyleSheet("border-image: url(:/newPrefix/picture/btn_on.png);")  ##修改camera_btn 样式
           self.camera_thread = CameraThread(self)  ##实例化摄像头线程
           self.camera_thread.signal.connect(self.show_camera)  ##线程信号与显示函数连接
           self.camera_thread.start()  ##开始摄像头线程
           self.num += 1
        else:
           self.camera_btn.setStyleSheet("border-image: url(:/newPrefix/picture/btn_off.png);")  ##修改camera_btn 样式
           self.label_info.setText('摄像头已关闭！')
           self.num = 0
           self.close_thread()

    def show_camera(self):
        """
        在label中显示摄像头
        :return:
        """
        try:
            if self.showImage:
                self.label_show_camera.setPixmap(self.showImage)  ##将摄像头获取到的图片展示在label上
        except Exception as e:
            print('camera show failed! :' + str(e))

    def close_thread(self):
        """
        关闭摄像头线程
        :return:
        """
        try:
            self.camera_thread.stop()
            self.camera_thread.quit()
            self.camera_thread.wait()
            self.camera_thread.exec_()
            self.camera_thread.exit()
            del self.camera_thread
        except:
            pass

class CameraThread(QThread):
    """
    调用摄像头线程
    """
    signal = QtCore.pyqtSignal(int)

    def __init__(self, page):
        self.page = page
        self.cap = cv2.VideoCapture(0)  # 开启摄像头
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))  ##格式
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.working = True
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        while self.working:
            try:
                ret, image = self.cap.read()  # 获取新的一帧图片
                if ret:
                    height, width, bytesPerComponent = image.shape  ##获取图片信息
                    bytesPerLine = bytesPerComponent * width
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  ##转为opencv可识别的rgb格式
                    showImage = QImage(rgb.data, width, height, bytesPerLine, QImage.Format_RGB888)  ##将图片转为QImage类型
                    self.page.showImage = QPixmap.fromImage(showImage)  ##将该图片传给界面里面的showImage
                    self.signal.emit(0)  ##发送触发信号
                else:
                    print('Open camera failed')
            except Exception as e:
                print('CameraThread error: ' + str(e))
                pass

    def stop(self):
        if self.working:
            self.working = False
            print('The CameraThread is quit!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    YQ_form_page = CameraPage()
    YQ_form_page.show()
    tcp_client = socket_client(host, port)  # 创建tcp　sockt 对象
    t1 = Thread(target=listen_server, args=(tcp_client,))  # 监听服务端发送数据
    t1.start()
    t2 = Thread(target=tcp_ping, args=(tcp_client,))  # 创建与云平台保持心跳的线程
    t2.start()
    sys.exit(app.exec_())