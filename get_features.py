import glob
import sys
import os
import cv2
import dlib
from landmarkPredict import getRGBTestPart,detectFace,batchRecoverPart
import caffe
import numpy as np
from sklearn.externals import joblib
vgg_height = 224
vgg_width = 224
pointNum =68


M_left = -0.15
M_right = +1.15
M_top = -0.10
M_bottom = +1.25




vgg_point_MODEL_FILE = 'model/deploy.prototxt'
vgg_point_PRETRAINED = 'model/68point_dlib_with_pose.caffemodel'
mean_filename='model/VGG_mean.binaryproto'
class Landmarks:
    def __init__(self,dir_path):
        self.dir_path = dir_path
        self.caffe_init()

    def caffe_init(self):
        self.vgg_point_net=caffe.Net(vgg_point_MODEL_FILE,vgg_point_PRETRAINED,caffe.TEST)
        caffe.set_mode_cpu()
        proto_data = open(mean_filename, "rb").read()
        self.a = caffe.io.caffe_pb2.BlobProto.FromString(proto_data)
        self.mean = caffe.io.blobproto_to_array(self.a)[0]

    def get_landmarks(self,image):
        bboxs = detectFace(image)
        faceNum = bboxs.shape[0]
        faces = np.zeros((1,3,vgg_height,vgg_width))
        predictpoints = np.zeros((faceNum,pointNum*2))
        predictpose = np.zeros((faceNum,3))
        imgsize = np.zeros((2))
        imgsize[0] = image.shape[0]-1
        imgsize[1] = image.shape[1]-1
        TotalSize = np.zeros((faceNum,2))
        landmarks = []
        colorface =None
        for i in range(0,faceNum):
            TotalSize[i] = imgsize
        for i in range(0,faceNum):
            bbox = bboxs[i]
            colorface = getRGBTestPart(bbox,M_left,M_right,M_top,M_bottom,image,vgg_height,vgg_width)
            normalface = np.zeros(self.mean.shape)
            normalface[0] = colorface[:,:,0]
            normalface[1] = colorface[:,:,1]
            normalface[2] = colorface[:,:,2]
            normalface = normalface - self.mean
            faces[0] = normalface

            blobName = '68point'
            data4DL = np.zeros([faces.shape[0],1,1,1])
            self.vgg_point_net.set_input_arrays(faces.astype(np.float32),data4DL.astype(np.float32))
            self.vgg_point_net.forward()
            predictpoints[i] = self.vgg_point_net.blobs[blobName].data[0]

            blobName = 'poselayer'
            pose_prediction = self.vgg_point_net.blobs[blobName].data
            predictpose[i] = pose_prediction * 50
            #pdb.set_trace()
        predictpoints = predictpoints * vgg_height/2 + vgg_width/2
        level1Point = batchRecoverPart(predictpoints,bboxs,TotalSize,M_left,M_right,M_top,M_bottom,vgg_height,vgg_width)

        landmarks.append([faceNum,level1Point,predictpose])
        return landmarks,colorface


def get_features(input_dir,output_dir,lnet):
    video_clips = glob.glob(os.path.join(input_dir,'*.avi'))
    
    for clip in video_clips:
        landmarks={}
        filename = os.path.split(clip)
        clip_name=filename[1].split('.')[0]
        landmarks['name'] = filename[1]
        print clip
        capture = cv2.VideoCapture(clip)
        nframes = capture.get(cv2.CAP_PROP_FPS )
        landmarks['nframes'] = nframes
        n=0
        print landmarks['name']
        while True:
            ret,frame = capture.read()
            if ret is not True:
                break
            n=n+1    
            print n,frame.shape
            lmarks = lnet.get_landmarks(frame)
            landmarks[n],face= lmarks
            image_name = '%s_%d.png' % (clip_name,n)
            cv2.imwrite(os.path.join(output_dir,"faces",image_name),face)
            #    print "frame %s has no  det" % n
                
        #print clip_name        
        clip_name = '%s' % clip_name
        joblib.dump(landmarks,os.path.join(output_dir, clip_name))
        












if __name__ == "__main__":
    if len(sys.argv) is not 3:
        print "Please provide the Input directory as argument"
        exit()
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    landmarks = Landmarks(input_dir)
    get_features(input_dir,output_dir,landmarks)
