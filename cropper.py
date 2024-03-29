import cv2
import dlib
import numpy as np
from imutils import face_utils
from scipy.spatial import distance

#使用dlib.get_frontal_face_detector()创建一个人脸检测器，用于在图像中找到人脸的位置
detector = dlib.get_frontal_face_detector()


#使用dlib.shape_predictor()创建一个人脸关键点预测器，用于在人脸上标记出68个特征点，如眼睛，鼻子，嘴巴等。
landmark_predictor = dlib.shape_predictor('./models/shape_predictor_68_face_landmarks.dat')


'''定义一个函数get_center，用于计算人脸关键点的中心位置。
参数shape是一个68x2的numpy数组，表示人脸的68个特征点的坐标。
计算shape数组的第一列（x坐标）的平均值，四舍五入，得到center_x。
计算shape数组的第二列（y坐标）的平均值，四舍五入，然后减去25，得到center_y。
返回center_x和center_y的元组。
'''
def get_center(shape):#计算关键点群的中心坐标
    center_x = int(round(np.sum(shape[:, 0]) / 68))
    center_y = int(round(np.sum(shape[:, 1]) / 68)) - 25
    return center_x, center_y
#其中round函数是用来四舍五入的
'''
# 四舍五入到整数
print(round(3.14159)) # 输出 3
# 四舍五入到一位小数
print(round(3.14159, 1)) # 输出 3.1
# 四舍五入到负一位
print(round(314.159, -1)) # 输出 310.0
'''

def crop_face(vc, norm_x, norm_y, vid_writer, crop_size=224):
    print('Crop face..')
    idx = 0
    scale_factor = None
    prev_center_x = None
    prev_center_y = None
    prev_roiX1 = None
    prev_roiY1 = None
    prev_roiX2 = None
    prev_roiY2 = None

    '''这段代码中的dlib_rects具体的值是一个包含多个dlib.rectangle对象的序列。每个dlib.rectangle对象表示一个人脸的矩形区域，包含左上角和右下角的坐标。例如，如果检测到了两个人脸，dlib_rects的值可能是：

    `[[(x1, y1) (x2, y2)], [(x3, y3) (x4, y4)]]`

    其中，(x1, y1)和(x2, y2)是第一个人脸的左上角和右下角的坐标，(x3, y3)和(x4, y4)是第二个人脸的左上角和右下角的坐标。
    '''
    while True:
        bgr_img = vc.read()[1]#vc.read()[0]返回的是TURE OR FALSE
        if bgr_img is None:
            break
        rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        # dlib face detection
        dlib_rects = detector(rgb_img, 1)  # dlib bbox detection

        list_dlib_rect = list(dlib_rects)


        # Exception handling 1: Detected more than one, find closest to given coordinate.
        if len(list_dlib_rect) > 1:
            frame_h, frame_w, _ = rgb_img.shape
            abs_x = round(norm_x * frame_w)
            abs_y = round(norm_y * frame_h)
            closest_rect = None
            closest_distance = 9999
            for k, rect in enumerate(list_dlib_rect):
                (x, y, w, h) = face_utils.rect_to_bb(rect)
                center_x = (x + (x + w)) / 2
                center_y = (y + (y + h)) / 2
                cur_distance = distance.euclidean((abs_x, abs_y), (center_x, center_y))
                if cur_distance < closest_distance:
                    closest_rect = rect
                    closest_distance = cur_distance
            list_dlib_rect = [closest_rect]

        # Predict landmark
        list_landmarks = []
        for rect in list_dlib_rect:
            shape = landmark_predictor(rgb_img, rect)
            list_points = list(map(lambda p: (p.x, p.y), shape.parts()))
            list_landmarks.append(list_points)
            shape = face_utils.shape_to_np(shape)
            center_x, center_y = get_center(shape)
            # Calculate inter-ocular distance at first detected frame and resize image.
            if scale_factor is None:
                left_eye_x = (shape[36][0] + shape[39][0]) / 2
                left_eye_y = (shape[38][1] + shape[40][1]) / 2
                right_eye_x = (shape[42][0] + shape[45][0]) / 2
                right_eye_y = (shape[43][1] + shape[46][1]) / 2
                interocular_distance = round(
                    distance.euclidean((left_eye_x, left_eye_y), (right_eye_x, right_eye_y)))
                scale_factor = 55 / interocular_distance
            rgb_img = cv2.resize(rgb_img, None, fx=scale_factor, fy=scale_factor)
            frame_h, frame_w, _ = rgb_img.shape
            abs_x = round(norm_x * frame_w)
            abs_y = round(norm_y * frame_h)

            # At first detected frame, set previous center coordinate as given coordinate
            if prev_center_x is None and prev_center_y is None:
                prev_center_x, prev_center_y = abs_x, abs_y

            center_x = round(center_x * scale_factor)
            center_y = round(center_y * scale_factor)

            # Exception handling 2: Detected face center is too far from previous frame's center.
            # There's a possibiliy that detected face is not target's.
            # 1. At first frame, skip this video
            # 2. or just use previous center as current frame's center.
            if abs(center_x - prev_center_x) > 62 or abs(center_y - prev_center_y) > 42:
                if idx == 0:
                    return False
                center_x = prev_center_x
                center_y = prev_center_y
            else:
                prev_center_x = center_x
                prev_center_y = center_y

        # Crop face and save landamrk.
        margin = int(crop_size / 2)
        if len(list_landmarks) != 0:
            roiX1 = center_x - margin if center_x - margin > 0 else 0
            roiY1 = center_y - margin if center_y - margin > 0 else 0
            roiX2 = center_x + margin if center_x + margin < rgb_img.shape[1] else rgb_img.shape[1]
            roiY2 = center_y + margin if center_y + margin < rgb_img.shape[0] else rgb_img.shape[0]
        else:
            # Exception handling 3: Detected nothing in,
            # 1. at (second to last) frame, use same ROI of previous frame.
            # 2. or, at frist frame, skip this video.
            if prev_roiX1 is not None:
                if scale_factor is not None:
                    rgb_img = cv2.resize(rgb_img, None, fx=scale_factor, fy=scale_factor)
                roiX1 = prev_roiX1
                roiY1 = prev_roiY1
                roiX2 = prev_roiX2
                roiY2 = prev_roiY2
            else:
                return False
        prev_roiX1 = roiX1
        prev_roiY1 = roiY1
        prev_roiX2 = roiX2
        prev_roiY2 = roiY2
        img_face = rgb_img[roiY1:roiY2, roiX1:roiX2].copy()
        img_face = cv2.cvtColor(img_face, cv2.COLOR_RGB2BGR)
        img_face = cv2.resize(img_face, (224, 224))
        vid_writer.write(img_face)
        idx += 1
    print('Cropping is done.')
    return True
