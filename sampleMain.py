from TFLite_detection_webcam_base import *

tfLiteDetector=TFLiteDetector(printFPS=True,use_TPU=False)
while True:
    detectedObjects=tfLiteDetector.getDetectedObjects()
    for object in detectedObjects:#object =(label, x, y, width, height)
        print("Location of {}:({},{})".format(object[0],object[1],object[2]))

tfLiteDetector.stop()