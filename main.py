import RPi.GPIO as GPIO
import camera
import util

#turn slowly until see target, p control to center, move forward while rudder correcting

#main state variable
#states include IDLE, SCAN, TURN, FORWARD, INTAKE 
state = "IDLE"

#device variables
cyclesPerCam = 10
cameraWidthPx = 1280 #?
targetPos = cameraWidthPx/2
trashFound = False
cycleCount = 0
errorTol = 40
defaultTurn = 0.3
maxCycles = 10000
error = 0
turnP = 0.1
rudderP = 0.1
forwardP = 0.1 

leftPIN = 17
rightPIN = 18

def setUpMotor(pin):
    GPIO.setup(pin, GPIO.OUT)
    d = GPIO.PWM(pin, 50)
    d.start(2.5)
    return d

def setMotorPowers(motor1, motor2):  
    setLeftMotor(motor1)
    setRightMotor(motor2)

def setMotorPower(side, power):
    if side == 0:
        leftMotor.changeDutyCycle(power)
    else: rightMotor.changeDutyCycle(power)

def setLeftMotor(power): setMotorPower(0,power)
def setRightMotor(power): setMotorPower(1,power)

def motorTurn(error = defaultTurn):
    setMotorPowers(error * turnP, -error * turnP)
    
def rudderTurn(error):
    setServoPos(error * rudderP)

def forward(size):
    setMotorPowers(size * turnP, size * turnP)

def setServoPos(pos):
    return 0

def charge():
    return 0

def intake(power):
    return 0


GPIO.setmode(GPIO.BCM)
leftMotor = setUpMotor(leftPIN)
rightMotor = setUpMotor(rightPIN)

while(True): #main control loop
    if cycleCount % cyclesPerCam == 0 : camera.cameraUpdate() #space out camera updates if its slow
                            
    relativePos = camera.getTrashMidline()
    error = targetPos - relativePos
    absError = abs(error)
  
    if state == "IDLE":
        setMotorPowers(0,0)
    elif state == "SCAN":
        motorTurn()
    elif state == "TURN":
        motorTurn(error)
    elif state == "FORWARD":
        forward(camera.getTrashSize())
        rudderTurn(error)
    elif state == "INTAKE":
        motorTurn()

    cycleCount += 1
    if(cycleCount > maxCycles):
        charge()
        break; #go to charge

