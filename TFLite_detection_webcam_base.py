# This program uses a TensorFlow Lite model to perform object detection on a live webcam
# feed. When the getDetectedObjects function is called after initialization, it returns
# a list of obejcts containing data about the detection.
# This code is based off Evan Juras's code for Webcam Object Detection Using Tensorflow-trained Classifier, as well as Tensorflow's sample code
#
import os
import argparse
import cv2
import numpy as np
import sys
import time
from threading import Thread
import importlib.util

class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(360,240),framerate=60):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])
            
        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

	# Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	# Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
	# Return the most recent frame
        return self.frame

    def stop(self):
	# Indicate that the camera and thread should be stopped
        self.stopped = True



class TFLiteDetector:
    """TFLiteDetector object that contains all the code for object detection"""
    def __init__(self,printFPS=True,use_TPU = True,resolution=(360,240),min_conf_threshold=0.5):
        MODEL_NAME = 'TFLiteModels'
        GRAPH_NAME = 'final_model.tflite'
        LABELMAP_NAME = 'labelmap.txt'
        self.printFPS=printFPS
        self.min_conf_threshold = min_conf_threshold
        resW, resH = resolution[0],resolution[1]
        self.imW, self.imH = int(resW), int(resH)
        

        # Import TensorFlow libraries
        # If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
        # If using Coral Edge TPU, import the load_delegate library
        pkg = importlib.util.find_spec('tflite_runtime')
        if pkg:
            from tflite_runtime.interpreter import Interpreter
            if use_TPU:
                from tflite_runtime.interpreter import load_delegate
        else:
            from tensorflow.lite.python.interpreter import Interpreter
            if use_TPU:
                from tensorflow.lite.python.interpreter import load_delegate

        # If using Edge TPU, assign filename for Edge TPU model
        if use_TPU:
            # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
            if (GRAPH_NAME == 'final_model.tflite'):
                GRAPH_NAME = 'final_model_edgetpu1.tflite'       

        # Get path to current working directory
        CWD_PATH = os.getcwd()

        # Path to .tflite file, which contains the model that is used for object detection
        PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

        # Path to label map file
        PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

        # Load the label map
        with open(PATH_TO_LABELS, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]

        # Have to do a weird fix for label map if using the COCO "starter model" from
        # https://www.tensorflow.org/lite/models/object_detection/overview
        # First label is '???', which has to be removed.
        if self.labels[0] == '???':
            del(self.labels[0])

        # Load the Tensorflow Lite model.
        # If using Edge TPU, use special load_delegate argument
        if use_TPU:
            self.interpreter = Interpreter(model_path=PATH_TO_CKPT,
                                    experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
            print(PATH_TO_CKPT)
        else:
            self.interpreter = Interpreter(model_path=PATH_TO_CKPT)

        self.interpreter.allocate_tensors()

        # Get model details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]

        self.floating_model = (self.input_details[0]['dtype'] == np.float32)

        self.input_mean = 127.5
        self.input_std = 127.5

        # Initialize frame rate calculation
        self.frame_rate_calc = 1
        self.freq = cv2.getTickFrequency()

        # Initialize video stream
        self.videostream = VideoStream(resolution=(self.imW,self.imH),framerate=60).start()
        time.sleep(1)

    """Returns list of tuples (label, x, y, width, height)"""  
    def getDetectedObjects(self):

        # Start timer (for calculating frame rate)
        t1 = cv2.getTickCount()

        # Grab frame from video stream
        frame1 = self.videostream.read()

        # Acquire frame and resize to expected shape [1xHxWx3]
        frame = frame1.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (self.width, self.height))
        input_data = np.expand_dims(frame_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if self.floating_model:
            input_data = (np.float32(input_data) - self.input_mean) / self.input_std

        # Perform the actual detection by running the model with the image as input
        self.interpreter.set_tensor(self.input_details[0]['index'],input_data)
        self.interpreter.invoke()

        # Retrieve detection results
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0] # Bounding box coordinates of detected objects
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0] # Class index of detected objects
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0] # Confidence of detected objects
        #num = self.interpreter.get_tensor(self.output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)

        objects=[]
        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(scores)):
            if ((scores[i] > self.min_conf_threshold) and (scores[i] <= 1.0)):

                # Get bounding box coordinates and draw box
                # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                ymin = int(max(1,(boxes[i][0] * self.imH)))
                xmin = int(max(1,(boxes[i][1] * self.imW)))
                ymax = int(min(self.imH,(boxes[i][2] * self.imH)))
                xmax = int(min(self.imW,(boxes[i][3] * self.imW)))

                # Draw label
                object_name = self.labels[int(classes[i])] # Look up object name from "labels" array using class index
                #label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'
                #labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                #label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
                #if object_name=="bottle":
                #cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)
                xCenter,yCenter=(xmin+xmax)/2,(ymin+ymax)/2
                boxWidth,boxHeight=(xmax-xmin),(ymax-ymin)
                #print(label, ", Center of bottle({},{})".format(xCenter,yCenter))
                #cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
                #cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text
                objects.append((object_name,xCenter,yCenter,boxWidth,boxHeight))

        # Draw framerate in corner of frame
        #v2.putText(frame,'FPS: {0:.2f}'.format(self.frame_rate_calc),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)
        if self.printFPS:
            print("FPS="+str(self.frame_rate_calc))
        # All the results have been drawn on the frame, so it's time to display it.
        #cv2.imshow('Object detector', frame)

        # Calculate framerate
        t2 = cv2.getTickCount()
        time1 = (t2-t1)/self.freq
        self.frame_rate_calc = 1/time1

        return objects 
        # Press 'q' to quit
        #if cv2.waitKey(1) == ord('q'):
            #break

    """Stop and clean up"""
    def stop(self):
        # Clean up
        cv2.destroyAllWindows()
        self.videostream.stop()

