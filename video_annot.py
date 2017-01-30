import cv2
import sys

WIN_NAME = "YawnDD"
Start_TRACKBAR = "Start_trackbar"
End_TRACKBAR = "End_trackbar"
Label_TRACKBAR = "0-Normal,1-Talking,2-Yawning"
CURRENT_FRAME_FLAG = cv2.CAP_PROP_POS_FRAMES
TOTAL_FRAMES_FLAG = cv2.CAP_PROP_FRAME_COUNT

class Annot:
    def __init__(self,clip_name):
        self.cap = cv2.VideoCapture(clip_name)
        self.start = 0
        self.end =0


    def create_window(self):
        cv2.namedWindow(WIN_NAME)
        cv2.createTrackbar(Start_TRACKBAR, WIN_NAME, 0, int(self.cap.get(TOTAL_FRAMES_FLAG)), self.seek_start_callback)
        cv2.createTrackbar(End_TRACKBAR, WIN_NAME, 0, int(self.cap.get(TOTAL_FRAMES_FLAG)), self.seek_end_callback)
        cv2.createTrackbar(Label_TRACKBAR, WIN_NAME, 0, 3, self.seek_label_callback)

    def seek_start_callback(self,x):
        i = cv2.getTrackbarPos(Start_TRACKBAR, WIN_NAME)
        self.start = i
        self.cap.set(CURRENT_FRAME_FLAG, i-1)
        _, self.frame = self.cap.read()
        cv2.imshow(WIN_NAME, self.frame)

    def seek_end_callback(self,x):
        i = cv2.getTrackbarPos(End_TRACKBAR, WIN_NAME)
        self.end = i
        self.cap.set(CURRENT_FRAME_FLAG, i-1)
        _, self.frame = self.cap.read()
        cv2.imshow(WIN_NAME, self.frame)
    
    def seek_label_callback(self,x):
        i = cv2.getTrackbarPos(End_TRACKBAR, WIN_NAME)
        self.label=i


    def show_clip(self):
        ret,self.frame = self.cap.read()
        while(True):
            cv2.imshow(WIN_NAME,self.frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break




if __name__ == "__main__":
    
    annot = Annot(sys.argv[1])
    annot.create_window()
    annot.show_clip()
