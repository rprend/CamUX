import os, sys

def launch():
    from circle_detector import CircleTracker
    import cv2
#    from pye3d_plugin import Pye3DPlugin

    circle_tracker = CircleTracker(0,0)
    cap = cv2.VideoCapture("sample_recording_v2/eye0.mp4")

    for x in range(100):
        sts, img = cap.read()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        circle_tracker.update(gray)
        cv2.imshow("img", gray)
        cv2.waitKey(1)


if __name__ == "__main__":
    launch()
