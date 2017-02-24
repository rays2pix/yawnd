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
import pdb

M_left = -0.15
M_right = +1.15
M_top = -0.10
M_bottom = +1.25



def get_opencv_version():
        version = cv2.__version__.split('.')
        if version[0] == '2':
            return 2
        else:
            return 3




vgg_point_MODEL_FILE = 'model/deploy.prototxt'
vgg_point_PRETRAINED = 'model/68point_dlib_with_pose.caffemodel'
mean_filename='model/VGG_mean.binaryproto'




class LNET:
    def __init__(self,dir_path):
        self.dir_path = dir_path
        self.caffe_init()

    def caffe_init(self):
        self.vgg_point_net=caffe.Net(vgg_point_MODEL_FILE,vgg_point_PRETRAINED,caffe.TEST)
        caffe.set_mode_gpu()
        proto_data = open(mean_filename, "rb").read()
        self.a = caffe.io.caffe_pb2.BlobProto.FromString(proto_data)
        self.mean = caffe.io.blobproto_to_array(self.a)[0]


class Landmarks:
    def __init__(self,num_frames):
        self.lmarks = np.zeros((num_frames,136))
        self.pose   = np.zeros((num_frames,3))
        self.isValid = np.zeros((num_frames,1))
        self.numFrames = num_frames
        self.bboxes = np.zeros((num_frames,4))


def extract_lmarks_batch(faces,lnet,bboxes):
    print faces.shape
    blobName = '68point'
    data4DL = np.zeros([faces.shape[0],1,1,1])
    lnet.vgg_point_net.set_input_arrays(faces.astype(np.float32),data4DL.astype(np.float32))
    lnet.vgg_point_net.forward()
    predictpoints = lnet.vgg_point_net.blobs[blobName].data
    blobName = 'poselayer'
    pose_prediction = lnet.vgg_point_net.blobs[blobName].data
    predictpose= pose_prediction * 50
    predictpoints = predictpoints * vgg_height/2 + vgg_width/2
    TotalSize = np.zeros([faces.shape[0],2])
    for i in range(faces.shape[0]):
        TotalSize[i][0]=480
        TotalSize[i][1]=640
    level1Points = batchRecoverPart(predictpoints,bboxes,TotalSize,M_left,M_right,M_top,M_bottom,vgg_height,vgg_width)

    return (level1Points,predictpose)


def getFaceRegion(frame,bbox,lnet):
    colorface = getRGBTestPart(bbox,M_left,M_right,M_top,M_bottom,frame,vgg_height,vgg_width)
    normalface = np.zeros(lnet.mean.shape)
    normalface[0] = colorface[:,:,0]
    normalface[1] = colorface[:,:,1]
    normalface[2] = colorface[:,:,2]
    normalface = normalface - lnet.mean
    return normalface

def get_features(clip,lnet,output_dir):
    filename = os.path.split(clip)
    clip_name=filename[1].split('.')[0]
    print filename
    cap = cv2.VideoCapture(clip)
    if get_opencv_version() == 3:
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    else:
        num_frames = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT) )
    print num_frames
    features = Landmarks(num_frames)

    i=0
    fnum =0 
    faces_batch = np.zeros((50,3,vgg_height,vgg_width))
    bbox_batch = np.zeros((50,4))
    while (fnum<num_frames):
        ret,frame = cap.read()
        if not ret:
            print "Error reading frame %d " % i
            continue
        bbox = detectFace(frame)
        numFaces = bbox.shape[0]
        if numFaces == 0:
            features.isValid[fnum] = 0
            faces_batch[i] = np.zeros((3,vgg_height,vgg_width))
        else:
            features.isValid[fnum] = 1
            faces_batch[i] = getFaceRegion(frame,bbox[0],lnet)
            bbox_batch[i] = bbox[0]

        i=i+1
        fnum = fnum +1
        print i,fnum
        if (fnum%50 == 0): 
           print i
           lm,poses = extract_lmarks_batch(faces_batch,lnet,bbox_batch)
           features.lmarks[fnum-50:fnum] = lm
           features.pose[fnum-50:fnum] =poses
           features.bboxes[fnum-50:fnum,:] = bbox_batch
           i=0

    if i<50:
        lm,poses = extract_lmarks_batch(faces_batch,lnet,bbox_batch)
        features.lmarks[num_frames-i:num_frames] = lm[:i,:]
        features.pose[num_frames-i:num_frames] =poses[:i,:]
    
    joblib.dump(features,os.path.join(output_dir, clip_name))
    return features



def checkIfProcessed(clip,output_dir):
    output_files = glob.glob(os.path.join(output_dir,'*'))
    output_files =[os.path.split(files)[-1] for files in output_files]
    #print output_files
    filename = os.path.split(clip)
    clip_name=filename[1].split('.')[0]
    return clip_name in output_files

def process_input_dir(input_dir,output_dir,lnet):
    video_clips = glob.glob(os.path.join(input_dir,'*.avi'))
    for clip in video_clips:
        if not  checkIfProcessed(clip,output_dir):
            print 'should process %s' % clip            
            features = get_features(clip,lnet,output_dir)



if __name__ == "__main__":
    if len(sys.argv) is not 3:
        print "Please provide the Input directory as argument"
        exit()
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    lnet = LNET(input_dir)
    process_input_dir(input_dir,output_dir,lnet)

