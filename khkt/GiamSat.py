# Su dung cac thu vien can thiet
# Su dung PushBullet de phat thong bao ve may tinh hoac dien thoai thong minh
import requests
import telepot
import cv2
import time
def ThongBao(msg):
    bot = telepot.Bot("")
    bot.sendMessage(657997660, msg)


def startRecord(duration=10, camera=0, output="output.mp4"):
    cap = cv2.VideoCapture(camera)
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"MP4V")
    out = cv2.VideoWriter(output, fourcc, 20.0, (640, 480))

    start_time = time.time()
    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if ret == True:
            frame = cv2.flip(frame, 0)

            # write the flipped frame
            out.write(frame)
        else:
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()


def takeScreenshot(camera=int):
    cap = cv2.VideoCapture(camera)
    ret, frame = cap.read()
    cv2.imwrite("screenshot.png", frame)
    cap.release()
