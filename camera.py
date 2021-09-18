import RPi.GPIO as GPIO
import time
from TFLite_detection_webcam_base import *

tfLiteDetector=TFLiteDetector(printFPS=True,use_TPU=False)

lastObject = 0
#label, x, y, width, height
def cameraUpdate():  
    detectedObjects=tfLiteDetector.getDetectedObjects()
    lastObject = detectedObjects[0]

def getTrashMidline():  
    return lastObject[1] + (lastObject[3]/2)

def getTrashSize():  
    return lastObject[3]
