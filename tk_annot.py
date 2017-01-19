from tkinter import *
from tkinter import ttk
import tkMessageBox
from tkinter import filedialog
import glob
import os
from PIL import Image
from PIL import ImageTk
import cv2
import numpy as np
from sklearn.externals import joblib
import pdb

class Annotator:
    def __init__(self):
        self.root = Tk()
        self.root.title("Yawdd Annotator")
        self.root.bind("<Left>",self.leftPress)
        self.root.bind("<Right>",self.rightPress)
        self.root.bind("<Up>",self.upPress)
        self.root.bind("<Down>",self.downPress)
        self.create_mainframes()
        self.create_button_widgets()
        self.create_image_widgets()
        self.create_scroll_widgets()
        self.current_clip = {} ## dict {'num_frames','name','annotations'}
        self.gt_dir = None
        self.cv2_version = self.get_opencv_version()

    def leftPress(self,event):
        print "Left key pressed" 

        frame_num = self.start_value.get()
        next_frame = np.round(frame_num) -1
        if next_frame < 0:
            next_frame =0
        self.current_clip['activeframe'] = next_frame
        self.start_value.set(next_frame)
        self.display_image() 


    def rightPress(self,event):
        print "Right key pressed" 
        frame_num = self.start_value.get()
        next_frame = np.round(frame_num) +1
        if next_frame < 0:
            next_frame =0
        self.current_clip['activeframe'] = next_frame
        self.start_value.set(next_frame)
        self.display_image() 

    def upPress(self,event):
        print "Up key pressed" 
        frame_num = self.stop_value.get()
        next_frame = np.round(frame_num) -1
        if next_frame < 0:
            next_frame =0
        self.current_clip['activeframe'] = next_frame
        self.stop_value.set(next_frame)
        self.display_image() 

    def downPress(self,event):
        print "Down key pressed" 
        frame_num = self.stop_value.get()
        next_frame = np.round(frame_num) +1
        self.current_clip['activeframe'] = next_frame
        self.stop_value.set(next_frame)
        self.display_image() 
        

    def get_opencv_version(self):
        version = cv2.__version__.split('.')
        if version[0] == '2':
            return 2
        else:
            return 3
    def create_mainframes(self):
        print "Creating all mainframes"
        buttons_frame = ttk.Frame(self.root,padding="3 3 12 12")
        buttons_frame.grid(column=0,row=0)
        buttons_frame.columnconfigure(0,weight=1)
        buttons_frame.rowconfigure(0,weight=1)

        image_frame = ttk.Frame(self.root,padding="3 3 12 12")
        image_frame.grid(column=0,row=1)
        image_frame.columnconfigure(0,weight=1)
        image_frame.rowconfigure(0,weight=1)


        scroll_frame = ttk.Frame(self.root,padding="3 3 12 12")
        scroll_frame.grid(column=0,row=2)
        scroll_frame.columnconfigure(0,weight=1)
        scroll_frame.rowconfigure(0,weight=1)


        self.buttons_frame = buttons_frame
        self.scroll_frame = scroll_frame
        self.image_frame = image_frame
   


    def get_active_frame(self):
        if self.current_clip['activeframe'] :
            return int(np.round(self.current_clip['activeframe']))
        else:
            return 1
         
    def display_image(self):
        if self.cv2_version == 3:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.get_active_frame())
        else:
            self.cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, self.get_active_frame())
        ret,frame = self.cap.read()
        if frame is None:
            print self.current_clip['activeframe'] , self.current_clip['num_frames']
            return
        print frame.shape
        tk_image = self.get_tk_image(frame)
        current_gt = self.current_clip['gt'][self.get_active_frame()]
        self.action.set(current_gt)
        self.image_label.configure(image = tk_image)
        self.image_label.image=tk_image
        
        ptr = self.start_value.get()
        print ptr
        #self.start_label.configure(text=ptr)
        ptr = self.stop_value.get()
        print ptr
        #self.stop_label.configure(text=ptr)

    def load_action(self):
        if self.gt_dir is None:
            tkMessageBox.showinfo("Error","Please select a ground truth directory before proceeding")
            self.current_clip['gt']=  [1] * (self.current_clip['num_frames'])
            return
        clip_name = self.current_clip_name.get()
        clip_name = clip_name.split('/')
        clip_name = clip_name[-1].split('.')[0]
        gt_path = os.path.join(self.gt_dir,clip_name)
        print clip_name
        if os.path.isfile(gt_path):
            self.current_clip['gt'] =  joblib.load(gt_path)
        else:
           self.current_clip['gt']=  [1] * self.current_clip['num_frames']

    def update_current_clip(self,clip_name):

        self.current_clip_name.set(clip_name)
        self.cap = cv2.VideoCapture(clip_name)

        if self.cv2_version == 3:
            num_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        else:
            num_frames = self.cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
        self.current_clip['num_frames'] = int(num_frames)
        self.current_clip['name'] =clip_name
        self.current_clip['activeframe']=0

        self.load_action()
        self.display_image()

        self.start_scale.configure(to=num_frames)
        self.stop_scale.configure(to=num_frames)
        self.start_value.set(0)
        self.stop_value.set(0)

    def dir_callback(self):
        self.source_dir = filedialog.askdirectory()
        self.video_files = glob.glob(os.path.join(self.source_dir,'*.avi'))
        print len(self.video_files)
        if len(self.video_files) <= 0:
            print "Bad directory,no video files"
        self.current_clip_index=0
        self.update_current_clip(self.video_files[self.current_clip_index]) 

        

        

    def gt_dir_callback(self):
        self.gt_dir = filedialog.askdirectory()
        self.load_action()

    def annotate(self):
        start = int(self.start_scale.get())
        stop  = int(self.stop_scale.get())
        print start,stop
        if start > stop:
            tkMessageBox.showerror("Error","Start frame should be less than stop frame")
            return
        self.current_clip['gt'][start:stop+1]= [self.action.get()] * (stop-start+1)



    def save_gt(self):
        if not self.gt_dir:
            print "Please select ground truth directory"
        clip_name = self.current_clip_name.get()
        clip_name = clip_name.split('/')
        clip_name = clip_name[-1].split('.')[0]
        gt_path = os.path.join(self.gt_dir,clip_name)
        print clip_name
        #gt_file = open(gt_path,'w')
        #for i,gt in enumerate(self.current_clip['gt']):
        #    gt_file.write(("%d,%d\n"%(i,gt)))
        #gt_file.close()
        joblib.dump(self.current_clip['gt'],gt_path)
        
    def get_next_clip(self):
        
        self.current_clip_index += 1
        if self.current_clip_index >= len(self.video_files):
            self.current_clip_name.set("End of directory..open another")
        else:
            self.current_clip_name.set(self.video_files[self.current_clip_index])
            self.update_current_clip(self.video_files[self.current_clip_index])

    def create_button_widgets(self):
        source_dir_button = ttk.Button(self.buttons_frame,text='Open Video Directory',command=self.dir_callback)
        source_dir_button.grid(column=0,row=0)
        source_dir_button.columnconfigure(0,weight=1)
        source_dir_button.rowconfigure(0,weight=1)
    
        gt_dir_button = ttk.Button(self.buttons_frame,text='Open ground truth Directory', command=self.gt_dir_callback)
        gt_dir_button.grid(column=2,row=0)
        gt_dir_button.columnconfigure(0,weight=1)
        gt_dir_button.rowconfigure(0,weight=1)

        radio_button_frame = ttk.Frame(self.buttons_frame)
        radio_button_frame.grid(row=2,column=0)
        self.action = IntVar()
        rb1 = ttk.Radiobutton(radio_button_frame, text="Normal", variable=self.action, value=1)
        rb1.grid(row=0,column=0)
        rb2 = ttk.Radiobutton(radio_button_frame, text="Talking", variable=self.action, value=2)
        rb2.grid(row=0,column=1)
        rb3 = ttk.Radiobutton(radio_button_frame, text="Yawn", variable=self.action, value=3)
        rb3.grid(row=0,column=2)
        self.action.set(3)
        self.current_clip_name = StringVar()
        self.current_clip_name.set("Select the video directory")
        clip_label = ttk.Label(self.buttons_frame,textvariable=self.current_clip_name)
        clip_label.grid(column=0,row=1,columnspan=2)
        clip_label.columnconfigure(0,weight=1)
        clip_label.rowconfigure(0,weight=1)



        next_button = ttk.Button(self.buttons_frame,text="Next",command=self.get_next_clip)
        next_button.grid(column=3,row=1)
        next_button.columnconfigure(0,weight=1)
        next_button.rowconfigure(0,weight=1)

        annotate_button = ttk.Button(self.buttons_frame,text="Annotate",command=self.annotate)
        annotate_button.grid(column=1,row=2)
        annotate_button.columnconfigure(0,weight=1)
        annotate_button.rowconfigure(0,weight=1)

        save_button = ttk.Button(self.buttons_frame,text="Save",command=self.save_gt)
        save_button.grid(column=2,row=2)
        save_button.columnconfigure(0,weight=1)
        save_button.rowconfigure(0,weight=1)


    def get_tk_image(self,image):
        pil_image = Image.fromarray(image)
        tk_image = ImageTk.PhotoImage(pil_image)
        return tk_image

    def move_frames_start(self,val):
        frame_num = self.start_value.get()
        self.current_clip['activeframe'] = np.round(float(val))
        self.display_image() 

    def move_frames_stop(self,val):
        self.current_clip['activeframe'] = np.round(float(val))
        self.display_image()


    def create_image_widgets(self):
        
        sample_image=cv2.imread('./yaww_sample.png')
        sample_image_tk = self.get_tk_image(sample_image)
        image_label = ttk.Label(self.image_frame,image=sample_image_tk)
        image_label.image=sample_image_tk
        image_label.grid(column=0,row=0,columnspan=3)
        image_label.columnconfigure(0,weight=1)
        image_label.rowconfigure(0,weight=1)

        self.image_label = image_label

    def create_scroll_widgets(self):
        start_label = ttk.Label(self.scroll_frame,text="Action Start")
        start_label.grid(row=0,column=0)
        self.start_value = IntVar()
        self.start_value.set(0)
        self.stop_value=IntVar()
        self.stop_value.set(10)
        ptr = self.start_value.get()
        start_value_label = ttk.Label(self.scroll_frame,textvariable=self.start_value,width=30)
        start_value_label.grid(row=0,column=1)
        start_scale = ttk.Scale(self.scroll_frame,orient = HORIZONTAL,length=700,from_=0,to=200,variable=self.start_value,command=self.move_frames_start)
        start_scale.grid(row=0,column=2)
        end_label = ttk.Label(self.scroll_frame,text="Action Stop")
        end_label.grid(row=1,column=0)

        ptr=self.stop_value.get() 
        end_value_label = ttk.Label(self.scroll_frame,textvariable=self.stop_value,width=30)
        end_value_label.grid(row=1,column=1)
        stop_scale = ttk.Scale(self.scroll_frame,orient = HORIZONTAL,length=700,from_=0,to=200,variable=self.stop_value,command=self.move_frames_stop)
        stop_scale.grid(row=1,column=2)
        self.stop_scale = stop_scale
        self.start_scale = start_scale
        self.start_label = start_value_label
        self.stop_label = end_value_label

    def mainloop(self):
        self.root.mainloop()




if __name__ == "__main__":
    yawddAnnotator = Annotator()
    yawddAnnotator.mainloop()
