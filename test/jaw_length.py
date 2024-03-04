import numpy as np
import os
import matplotlib.pyplot as plt
import warnings
import cv2
from facexlib.alignment import init_alignment_model

warnings.filterwarnings('ignore')
plt.rcParams["axes.labelsize"]=14
plt.rcParams["xtick.labelsize"]=12
plt.rcParams['ytick.labelsize']=12
np.random.seed(42)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


vid_pth = '../data/5f2b6837d4c6aa9850637689d6bd287e.mp4'
face_align = init_alignment_model('awing_fan', model_rootpath='../weights')

def show_jaw_length(vid_pth):
    video_stream = cv2.VideoCapture(vid_pth)#获得视频流
    jaws_len=[]#创建存放每帧下巴长度的列表
    average_jaw_length = 0#创建平均下巴长度变量
    #while循环一帧一帧处理
    while True:
        ret, frame = video_stream.read()#获得某一帧
        if not ret:
            break
        lmds = face_align.get_landmarks(frame)#获得98个人脸关键点的二维数组
        jaw_len = lmds[16][1]-lmds[85][1]#根据关键点计算当前帧的下巴长度
        jaws_len.append(jaw_len)#存入下巴长度列表
        average_jaw_length += jaw_len
    video_stream.release()
    average_jaw_length = average_jaw_length/len(jaws_len)


    index_list = []
    value_list = []
    for index, value in enumerate(jaws_len):
        index_list.append(index)
        value_list.append(value)


    plt.plot(index_list, value_list, marker='o', linestyle='-', color='b', label='jaw_length')
    plt.axhline(y=average_jaw_length, color='r', linestyle='--', label='average_jaw_length')

    # 添加标题和标签
    plt.title('jaw_length')
    plt.xlabel('time')
    plt.ylabel('jaw_length')

    # 添加图例
    plt.legend()

    # 显示图形
    plt.show()

if __name__ == '__main__':
    show_jaw_length(vid_pth)