# FIRSTGlobalProject2021
The official repository for the code for the Team USA-Team Zimbabwe Alliance in the 2021 FIRST Global Challenge.

# Usage
## Run with Monitor and i/o to Raspberry Pi
1. Setup the Pi by connecting it to a monitor, mouse, and keyboard
2. Open the command line.
3. Type 
    ```
    cd FirstGlobalProject2021
    source FGCProject/bin/activate
    python samplemain.py
    ```
## Set up SSH remote connection and run remotely

#### On raspberry Pi
1. Connect raspberry pi to a wifi network(https://www.raspberrypi.org/forums/viewtopic.php?t=217544). Make sure the laptop you want to use is connected to that same network.
2. Type “ifconfig”
3. Find where it says, “inet” followed by an ip address

#### On your Laptop:
1. Download VS Code and the SSH extension. SSH in with the extension to pi@{insert the ip address you saw earlier here}
2. When prompted for a password, type raspberry
3. The repo should be already cloned. On a terminal, type
   ```
    cd FirstGlobalProject2021
    source FGCProject/bin/activate
    ```
4. Open `main.py` in VS Code and replace the ports for the motors with the ports connected in your Raspberry Pi. 
5. Type `python main.py` to run.

# About
## Machine learning object detection
We are using EfficientNet for object detection. The EfficientNet model with our custom training provides highly efficient and accurate detection of plastic waste in water environments. For an ordinary raspberry pi, this model has an typical inference time of 200-300 milliseconds.  Through the integration of a Google Coral TPU (Tensor Processing Unit) accelerator, we were able to achieve accurate inferencing in just under 40 milliseconds.
We have multiple models, all contained in the /TFLiteModels folder. The base class for running these models is the TFLite_detection_webcam_base.py file.

This model is not only able to detect where the waste is, but also detect what kind of waste there is, to avoid collecting organic items floating on the water, as those items could be part of marine life’s natural habitat. Plastic waste that endangers animals and the environment is targeted, and the robot collects all plastic waste visible.
This is acomplished with code in the main.py file, and the sampleMain.py file offers an example of how to call the base detection class.

## Trash collection
Our Pirate Robot can operate in an autonomous mode and a manual control mode. In the autonomous mode, the robot in its normal state slowly spins and scans around in the water. When the AI model detects plastic waste to be picked up, it then slowly moves towards the waste, intaking once it gets close enough. The robot then repeats this algorithm.

