# -*- coding: utf-8 -*-
#!/usr/bin/env python3.5
# Cách sử dụng, gõ dòng lệnh sau lên terminal
# python multidetection.py
# Tải các thư viện cần thiết
from __future__ import print_function
import warnings
import datetime
import json
import time
from imutils.video import FPS
from imutils.video import VideoStream
import dropbox
import cv2
import imutils
from pyimagesearch.tempimage import TempImage
from khkt import GiamSat

# Lọc các cảnh bảo, tải cấu hình
warnings.filterwarnings("ignore")
client = None
conf = json.load(open("conf.json"))

# Kiểm tra xem có nên dùng dropbox không
if conf["use_dropbox"]:
    # Kết nối đến Dropbox và bắt đầu quá trình đăng nhập
    client = dropbox.Dropbox(conf["dropbox_access_token"])
    print("[Thông báo] Kết nối thành công đến tài khoản Dropbox")

# Khởi động camera kết hợp với tính năng chạy đa luồng
print("Đang khởi động camera 1..")
stream1 = VideoStream(src=0).start()
time.sleep(conf["camera_warmup_time"])
print("Đang khởi động camera 2..")
stream2 = VideoStream(src=1).start()
time.sleep(conf["camera_warmup_time"])

# Bắt đầu bộ đếm FPS
fps = FPS().start()

# Tạo một biến để lưu giữ khung hình đầu tiên của camera 1 và 2
firstFrame1 = None
firstFrame2 = None
# Lấy thời giạn lần cuối ảnh được tải lên lần lượt từ camera 1 và 2
lastUploaded1 = datetime.datetime.now()
lastUploaded2 = datetime.datetime.now()
# Bộ đếm chuyển động cho camera 1 và 2
motionCounter1 = 0
motionCounter2 = 0
# Bắt đầu vòng lặp
while True:
    frame1 = stream1.read()
    frame2 = stream2.read()
    timestamp1 = datetime.datetime.now()
    timestamp2 = datetime.datetime.now()
    text1 = "Khong phat hien chuyen dong"
    text2 = "Khong phat hien chuyen dong"
    # Chỉnh chiều rộng khung hình camera 1 và 2, Rộng = 400
    frame1 = imutils.resize(frame1, width=400)
    frame2 = imutils.resize(frame2, width=400)
    # Sử dụng hàm cvtColor để chuyển khung hình camera 1 và 2 thành màu xám
    # để biến đổi khung hình về một ma trận số hai chiều duy nhất thay vì nhiều ma trận số làm mất thời gian.
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    # Làm mờ hình ảnh bằng hàm Gaussian để giảm nhiễu ảnh
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

    # Nếu cả 2 camera chưa có khung hình đầu tiên thì nhét khung hình đầu tiên vào firstFrame
    if firstFrame1 is None:
        firstFrame1 = gray1
        continue
    if firstFrame2 is None:
        firstFrame2 = gray2
        continue
    # So sánh sự khác nhau giữa khung hình đầu tiên và khung hình hiện tại để tìm sự khác biệt
    # frameDelta = Khung hình đầu tiên - Khung hình hiện tại
    frameDelta1 = cv2.absdiff(firstFrame1, gray1)
    frameDelta2 = cv2.absdiff(firstFrame2, gray2)
    # Sử dụng kỹ thuật thresholding để lọc từng pixel của một hình ảnh đen trắng
    # theo một ngưỡng nào đó. Ngưỡng hiện tại là 25
    thresh1 = cv2.threshold(
        frameDelta1, conf["delta_thresh_cam1"], 255, cv2.THRESH_BINARY)[1]
    thresh2 = cv2.threshold(
        frameDelta2, conf["delta_thresh_cam2"], 255, cv2.THRESH_BINARY)[1]
    # Sử dụng hàm dilate để làm đối tượng giãn nở ra
    # có tác dụng làm cho đối tượng ban đầu tăng lên (giãn nở) về kích thước
    thresh1 = cv2.dilate(thresh1, None, iterations=2)
    thresh2 = cv2.dilate(thresh2, None, iterations=2)
    # Sử dụng hàm tìm biên dạng để tìm đường viền của đối tượng
    cnts1 = cv2.findContours(
        thresh1.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts1 = cnts1[0] if imutils.is_cv2() else cnts1[1]
    cnts2 = cv2.findContours(
        thresh2.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts2 = cnts2[0] if imutils.is_cv2() else cnts2[1]

    # Sau khi đã có được các viền của các đối tượng,
    # chúng ta tiến hành tìm điểm chính giữa và vẽ nó vào vị trí tương ứng với từng đối tượng
    for c1 in cnts1:
        # Nếu đường viền quá nhỏ so với min area thì bỏ qua
        if cv2.contourArea(c1) < conf["min_area"]:
            continue

        # Tạo một ô vuông quanh đường viền và vẽ nó lên khung hình
        (x, y, w, h) = cv2.boundingRect(c1)
        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Cập nhật dòng chữ để cảnh báo người dùng
        text1 = "Phat hien chuyen dong"
        if conf["use_telegram"]:
            GiamSat.ThongBao("Camera 1 phát hiện chuyển động")

    for c2 in cnts2:
        # Nếu đường viền quá nhỏ so với min area thì bỏ qua
        if cv2.contourArea(c2) < conf["min_area"]:
            continue

        # Tạo một ô vuông quanh đường viền và vẽ nó lên khung hình
        (x2, y2, w2, h2) = cv2.boundingRect(c2)
        cv2.rectangle(frame2, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 0), 2)
        # Cập nhật dòng chữ để cảnh báo người dùng
        text2 = "Phat hien chuyen dong"
        if conf["use_telegram"]:
            GiamSat.ThongBao("Camera 2 phát hiện chuyển động")

    # Ghi ảnh và thời gian hiện tai lên góc trái khung hình
    ts = timestamp1.strftime("%A %d %B %Y %I:%M:%S%p")
    textColor = int

    if text1 == "Khong phat hien chuyen dong":
        textColor1 = (255, 255, 255)
    else:
        textColor1 = (0, 0, 255)
    if text2 == "Khong phat hien chuyen dong":
        textColor2 = (255, 255, 255)
    else:
        textColor2 = (0, 0, 255)
    cv2.putText(
        img=frame1,
        text="Tinh trang: {}".format(text1),
        org=(10, 20),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.5,
        color=textColor1,
        thickness=1,
    )
    cv2.putText(
        img=frame1,
        text=datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
        org=(10, frame1.shape[0] - 10),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.35,
        color=textColor1,
        thickness=1,
    )

    cv2.putText(
        img=frame2,
        text="Tinh trang: {}".format(text2),
        org=(10, 20),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.5,
        color=textColor2,
        thickness=1,
    )
    cv2.putText(
        img=frame2,
        text=datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
        org=(10, frame2.shape[0] - 10),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.35,
        color=textColor2,
        thickness=1,
    )

    # Nếu phát hiện chuyển động thì chụp lại và tải lên Dropbox
    if text1 == "Phat hien chuyen dong":
        # kiểm tra xem đã đủ thời gian trôi qua giữa các lần tải lên chưa
        if (timestamp1 - lastUploaded1).seconds >= conf["min_upload_seconds"]:
            # tăng bộ đếm chuyển động lên 1 lần
            motionCounter1 += 1
            # Kiểm tra xem số lượng khung hình có chuyển động đã đủ cao chưa
            # Ngưỡng hiện tại là 8 khung hình
            if motionCounter1 >= conf["min_motion_frames_cam1"]:
                # Kiểm tra xem có nên dùng Dropbox hay không
                if conf["use_dropbox"]:
                    # Viết ảnh ra một file tạm thời
                    t = TempImage()
                    cv2.imwrite(t.path, frame1)
                    # Gửi ảnh lên Dropbox và xoá những file tạm thời
                    print("[Camera_1 - UPLOAD] {}".format(ts))
                    path = "/{base_path}/cam1/Camera1_{timestamp}.jpg".format(
                        base_path=conf["dropbox_base_path"], timestamp=ts
                    )
                    client.files_upload(open(t.path, "rb").read(), path)
                    t.cleanup()

                # Cập nhật thời gian lần cuối ảnh được tải lên
                lastUploaded1 = timestamp1
                # Cài lại bộ đếm chuyển động
                motionCounter1 = 0

    # Nếu không thì không phát hiện chuyển động
    else:
        motionCounter1 = 0

    # Nếu phát hiện chuyển động thì chụp lại và tải lên Dropbox
    if text2 == "Phat hien chuyen dong":
        # kiểm tra xem đã đủ thời gian trôi qua giữa các lần tải lên chưa
        if (timestamp2 - lastUploaded2).seconds >= conf["min_upload_seconds"]:
            # tăng bộ đếm chuyển động lên 1 lần
            motionCounter2 += 1
            # Kiểm tra xem số lượng khung hình có chuyển động đã đủ cao chưa
            # Ngưỡng hiện tại là 8 khung hình
            if motionCounter2 >= conf["min_motion_frames_cam2"]:
                # Kiểm tra xem có nên dùng Dropbox hay không
                if conf["use_dropbox"]:
                    # Viết ảnh ra một file tạm thời
                    t2 = TempImage()
                    cv2.imwrite(t2.path, frame2)
                    # Gửi ảnh lên Dropbox và xoá những file tạm thời
                    print("[Camera_2 - UPLOAD] {}".format(ts))
                    path = "/{base_path}/cam2/Camera2_{timestamp}.jpg".format(
                        base_path=conf["dropbox_base_path"], timestamp=ts
                    )
                    client.files_upload(open(t2.path, "rb").read(), path)
                    t2.cleanup()

                # Cập nhật thời gian lần cuối ảnh được tải lên
                lastUploaded2 = timestamp2
                # Cài lại bộ đếm chuyển động
                motionCounter2 = 0

    # Nếu không thì không phát hiện chuyển động
    else:
        motionCounter2 = 0

    # Kiểm tra xem có nên hiển thị video lên màn hình không
    if conf["show_video"]:
        # Truyền video lên cửa sổ
        cv2.imshow("Camera 1", frame1)
        cv2.imshow("Camera 2", frame2)
        cv2.moveWindow("Camera 1", 0, 0)
        key = cv2.waitKey(1) & 0xFF
        fps.update()

        # Nếu nhấn q thì dừng quay video
        if key == ord("q"):
            break

# stop the timer and display FPS information
fps.stop()
print("[INFO] Thời gian đã trôi qua: {:.2f}".format(fps.elapsed()) + " Giây")
print("[INFO] Chỉ số FPS trung bình là: {:.2f}".format(fps.fps()))
# Dừng 2 camera lại và đóng tất cả cửa sổ
stream1.stop()
stream2.stop()
cv2.destroyAllWindows()
