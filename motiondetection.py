# -*- coding: utf-8 -*-
#!/usr/bin/env python3.5
# Cách sử dụng, gõ dòng lệnh sau lên terminal
# python motion_detector.py --conf conf.json
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

# Min area mặc định trong conf.json là 5000 có thể chỉnh lại thành 500

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
print("Đang khởi động camera..")
# Đọc trực tiếp video truyền từ camera
stream = VideoStream(src=0).start()
time.sleep(conf["camera_warmup_time"])
# Bắt đầu bộ đếm FPS
fps = FPS().start()

# Khởi chạy khung hình đầu tiên trên video
firstFrame = None
lastUploaded = datetime.datetime.now()
motionCounter = 0

# Bắt đầu vòng lặp
while True:
    # Dọc các khung hình video được truyền từ camera
    frame = stream.read()
    timestamp = datetime.datetime.now()
    text = "Khong phat hien chuyen dong"

    # Nếu không dùng được khung hình hiện tại thì dừng quay video
    if frame is None:
        break

    # Chỉnh chiều rộng video, chuyển đổi sang màu xám và làm mờ đi
    frame = imutils.resize(frame, width=400)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Nếu khung hình đầu tiền là None, thì khởi chạy nó
    if firstFrame is None:
        firstFrame = gray
        continue

    # So sánh sự khác nhau giữa khung hình hiện tại và khung hình ban đầu
    frameDelta = cv2.absdiff(firstFrame, gray)
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    #
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]

    # Tạo vòng lặp
    for c in cnts:
        # Nếu đường viền quá nhỏ thì bỏ qua
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        # Tạo một ô vuông quanh đường viền và vẽ nó lên khung hình
        # Cập nhật dòng chữ để cảnh báo người dùng
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Phat hien chuyen dong"
        if conf["use_telegram"]:
            GiamSat.ThongBao("Camera phát hiện chuyển động")

    # Ghi ảnh và thời gian hiện tai lên góc trái khung hình
    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    textColor = int

    if text == "Khong phat hien chuyen dong":
        textColor = (255, 255, 255)
    else:
        textColor = (0, 0, 255)

    cv2.putText(
        img=frame,
        text="Tinh trang: {}".format(text),
        org=(10, 20),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.5,
        color=textColor,
        thickness=1,
    )
    cv2.putText(
        img=frame,
        text=datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
        org=(10, frame.shape[0] - 10),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.35,
        color=textColor,
        thickness=1,
    )

    # Nếu phát hiện chuyển động thì chụp lại và tải lên Dropbox
    if text == "Phat hien chuyen dong":
        # check to see if enough time has passed between uploads
        if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
            # increment the motion counter
            motionCounter += 1

            # check to see if the number of frames with consistent motion is
            # high enough
            if motionCounter >= conf["min_motion_frames"]:
                # Kiểm tra xem có nên dùng Dropbox hay không
                if conf["use_dropbox"]:
                    # Viết ảnh ra một file tạm thời
                    t = TempImage()
                    cv2.imwrite(t.path, frame)

                    # Gửi ảnh lên Dropbox và xoá những file tạm thời
                    print("[UPLOAD - Camera1] {}".format(ts))
                    path = "/{base_path}/{timestamp}.jpg".format(
                        base_path=conf["dropbox_base_path"], timestamp=ts
                    )
                    client.files_upload(open(t.path, "rb").read(), path)
                    t.cleanup()

                # update the last uploaded timestamp and reset the motion
                # counter
                lastUploaded = timestamp
                motionCounter = 0

    # otherwise, the room is not occupied
    else:
        motionCounter = 0

    # Kiểm tra xem có nên hiển thị video lên màn hình không
    if conf["show_video"]:
        # Truyền video lên cửa sổ
        cv2.imshow("Camera 1", frame)
        cv2.moveWindow("Camera 1", 0, 0)
        key = cv2.waitKey(1) & 0xFF
        fps.update()

        # Nếu nhấn ESC thì dừng quay video
        if key == 27:
            break

# stop the timer and display FPS information
fps.stop()
print("[INFO] Thời gian đã trôi qua: {:.2f}".format(fps.elapsed()) + " Giây")
print("[INFO] Chỉ số FPS trung bình là: {:.2f}".format(fps.fps()))
# Dừng camera lại và đóng tất cả cửa sổ
stream.stop()
cv2.destroyAllWindows()
