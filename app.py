from green import findGreen
from arm import Ports, Arm
import cv2
import base64
import os
import multiprocessing as mp
import time
import socket
import ctypes
import yaml
import math

PORT = mp.Array(ctypes.c_char, 50, lock=False)
Cx = mp.Value(ctypes.c_int, 0)
Cy = mp.Value(ctypes.c_int, 0)
imgX = mp.Value(ctypes.c_int, 0)
imgY = mp.Value(ctypes.c_int, 0)
MANUAL_MODE = mp.Value(ctypes.c_int, 1)
CALIBRATIONS = {}

def receiveCommands(sock:socket.socket, PORT, MANUAL_MODE):
    while True:
        try:
            raw_com = sock.dup().recv(1024).decode().replace("\n", "").strip()
            com = raw_com[:3]
            args = raw_com[3:]
            print(com, args)
            if com == "CON":
                PORT.value = args.encode()
            elif com == "MAN":
                MANUAL_MODE.value = int(args)
            else:
                pass
            
            time.sleep(.1)
        
        except Exception as e:
            return

def sendCapture(index:int, conn:socket.socket, PORT, Cx, Cy, MANUAL_MODE, imgX, imgY):
    cap = cv2.VideoCapture(index) # Open the camera
    newconn, addr = conn.accept()
    
    p = mp.Process(target=receiveCommands, args=(newconn, PORT, MANUAL_MODE,))
    p.start()
    
    while(cap.isOpened()):
        _, img = cap.read() # Read camera
        Cx.value, Cy.value, img = findGreen(img, Cx.value, Cy.value) # Find green
        
        imgX.value = len(img)
        imgY.value = len(img[0])
        
        _, buffer = cv2.imencode('.jpg', img) # Encode as JPEG
        base64_image = base64.b64encode(buffer) # Encode as base64
        
        # Store previously sent data to avoid repetition
        prevCXD = ""
        prevCYD = ""
        prevPRT = ""
        prevPRS = ""
        prevMAN = ""
        
        # Send data
        try:
            # Send webcam feed
            newconn.send(("IMG" + base64_image.decode() + "\n").encode())
            cv2.waitKey(1)
            
            # Send Cx
            CXD = str(Cx.value)
            if CXD != prevCXD:
                newconn.send(("CXD" + CXD + "\n").encode())
                prevCXD = CXD
                cv2.waitKey(1)
            
            # Send Cy
            CYD = str(Cy.value)
            if CYD != prevCYD:
                newconn.send(("CYD" + CYD + "\n").encode())
                prevCYD = CYD
                cv2.waitKey(1)
            
            # Send connected port
            PRT = PORT.value.decode()
            if PRT != prevPRT:
                newconn.send(("PRT" + PRT + "\n").encode())
                prevPRT = PRT
                cv2.waitKey(1)
            
            # Send ports list
            PRS = "|".join(Ports.list())
            if PRS != prevPRS:
                newconn.send(("PRS" + PRS + "\n").encode())
                prevPRS = PRS
                cv2.waitKey(1)
            
            # Send manual mode status
            MAN = str(MANUAL_MODE.value)
            if MAN != prevMAN:
                newconn.send(("MAN" + MAN + "\n").encode())
                prevMAN = MAN
                cv2.waitKey(1)
            
            
            #cv2.imshow("HELLO", img)
        except Exception as e:
            newconn, addr = conn.accept()
            p.kill()
            p = mp.Process(target=receiveCommands, args=(newconn, PORT,))
            p.start()
            print(e)
        
        

def startWebserver():
    os.system("go run main.go")
    
def calibrate() -> dict:
    """Reload calibrations file"""
    global CALIBRATIONS
    with open("calibration.yaml", "r") as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
        CALIBRATIONS = data
        return data
    
def strip_PWM(steps:int, time:int, Vin:float, Vout:float) -> tuple[int, float, float]:
    """Converts PWM to the format desired by arm.py"""
    uptime = (Vout * time) / (Vin * steps)
    downtime = time / steps - uptime
    return (steps, uptime, downtime)

def hardware_step(component:str, index:int) -> tuple[int, float, float]:
    return strip_PWM(int(CALIBRATIONS["hardware"][index][component][0]["steps"]), int(CALIBRATIONS["hardware"][index][component][1]["time"]), float(CALIBRATIONS["hardware"][index][component][2]["Vin"]), float(CALIBRATIONS["hardware"][index][component][3]["Vout"]))

def hardware_limit(component:str, index:int) -> (int | bool):
    return CALIBRATIONS["hardware"][index][component][4]["limit"]

class Convert():
    """Used to convert physical units"""
    # Time conversions
    def micros_to_sec(micros:float) -> float: return micros / 1000000
    def micros_to_milis(micros:float) -> float: return micros / 1000
    def milis_to_sec(milis:float) -> float: return milis / 1000
    def milis_to_micros(milis:float) -> float: return milis * 1000
    def secs_to_milis(secs:float) -> float: return secs * 1000
    def secs_to_micros(secs:float) -> float: return secs * 1000000

if __name__ == '__main__':
    # Start the webserver
    p = mp.Process(target=startWebserver)
    p.start()
    time.sleep(2)
    print("sending")
    
    # Make TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 8888))
    server_socket.listen()
    
    # Start sending and receiving data
    p = mp.Process(target=sendCapture, args=(1, server_socket, PORT, Cx, Cy, MANUAL_MODE, imgX, imgY,))
    p.start()
    
    # Load calibrations
    calibrate()
    #print(CALIBRATIONS)
    print(hardware_step("rotation", 0))
    print(hardware_step("uplift", 1))
    print(hardware_step("extend", 2))
    
    # Use the data we got
    arduino = None
    current_port = ""
    rot_index, up_index, extend_index = 0, 0, 0
    while True:
        # Recalibrate
        if CALIBRATIONS["active_debugging"]:
            calibrate()
        
        # Change the port on the fly
        if current_port != PORT.value.decode():
            print("PORT CHANGED")
            try:
                arduino = Arm(PORT.value.decode())
                current_port = PORT.value.decode()
                
                # Move everything to a known position
                # build rotation
                max_time = 0
                rot_com, up_com, ext_com = ("", "", "")
                if type(hardware_limit("rotation", 0)) == bool:
                    rot_com = f"-1:{Convert.secs_to_micros(5)}:0"
                    if max_time < Convert.secs_to_micros(5): max_time = Convert.secs_to_micros(5)
                else:
                    limit = hardware_limit("rotation", 0)
                    com = hardware_step("rotation", 0)
                    rot_com = f"-{com[0]*limit}:{round(com[1])}:{round(com[2])}"
                    if max_time < (com[1]+com[2])*com[0]*limit: max_time = (com[1]+com[2])*com[0]*limit
                    
                print(max_time)
                    
                # build uplift
                if type(hardware_limit("uplift", 1)) == bool:
                    up_com = f"-1:{Convert.secs_to_micros(25)}:0"
                    if max_time < Convert.secs_to_micros(25): max_time = Convert.secs_to_micros(25)
                else:
                    limit = hardware_limit("uplift", 1)
                    com = hardware_step("uplift", 1)
                    up_com = f"{com[0]*limit}:{round(com[1])}:{round(com[2])}"
                    if max_time < (com[1]+com[2])*com[0]*limit: max_time = (com[1]+com[2])*com[0]*limit
                    
                print(max_time)
                
                # build extend
                if type(hardware_limit("extend", 2)) == bool:
                    ext_com = f"-1:{Convert.secs_to_micros(25)}:0"
                    if max_time < Convert.secs_to_micros(25): max_time = Convert.secs_to_micros(25)
                else:
                    limit = hardware_limit("extend", 2)
                    com = hardware_step("extend", 2)
                    ext_com = f"-{com[0]*limit}:{round(com[1])}:{round(com[2])}"
                    if max_time < (com[1]+com[2])*com[0]*limit: max_time = (com[1]+com[2])*com[0]*limit
                    
                print(max_time)
                    
                # Apply commands and wait for them to finish
                arduino.slave_command([rot_com, up_com, ext_com])
                print(f"Waiting {Convert.micros_to_sec(max_time)} seconds")
                time.sleep(Convert.micros_to_sec(max_time))
                
                # Reset indexes
                rot_index, up_index, extend_index = 0, hardware_limit("uplift", 1), 0
                
            except Exception as e:
                print(e)
                current_port = ""
                PORT.value = b''
        
        # If no port is connected, no reason to continue
        if current_port == "":
            continue
        
        # Execute automations
        if MANUAL_MODE.value == 0:
            # Extract calibration data
            max_deviation = CALIBRATIONS["software"][0]["max_deviation"]
            offset_x, offset_y = CALIBRATIONS["software"][1]["center_offset"][0]["x"], CALIBRATIONS["software"][1]["center_offset"][1]["y"]
            
            # Calculate values
            imgCx, imgCy = imgX.value / 2, imgY.value / 2
            imgdsq = (imgX.value + imgY.value) / 2
            
            # Apply offsets
            imgCx += offset_x / 100 * imgX.value
            imgCy += offset_y / 100 * imgY.value
            
            # Deviation
            distance = math.sqrt((Cx.value - imgCx)**2 + (Cy.value - imgCy)**2)
            deviation = distance / imgdsq * 100
            
            # Check if we can pick up this object
            if deviation <= max_deviation:
                print("Object alligned")
                # Collapse uplift
                com = hardware_step("uplift", 1)
                up_com = f"-{com[0]*up_index}:{round(com[1])}:{round(com[2])}"
                arduino.slave_command(["", up_com])
                
                # How much time to wait
                print("Collapsing uplift")
                t = (com[1]+com[2])*com[0]*up_index
                time.sleep(Convert.micros_to_sec(t))
                
                # Close gripper
                print("Closing gripper")
                arduino.slave_command(["", "", "", "1:0:0"])
                time.sleep(1)
                
                # Extend uplift
                com = hardware_step("uplift", 1)
                up_com = f"{com[0]*up_index}:{round(com[1])}:{round(com[2])}"
                arduino.slave_command(["", up_com])
                
                # How much time to wait
                print("Extending uplift")
                t = (com[1]+com[2])*com[0]*up_index
                time.sleep(Convert.micros_to_sec(t))
                
                # Rotate to start position
                com = hardware_step("rotation", 0)
                rot_com = f"-{com[0]*rot_index}:{round(com[1])}:{round(com[2])}"
                arduino.slave_command([rot_com])
                rot_index = 0
                
                # How much time to wait
                print("Rotating to start position")
                t = (com[1]+com[2])*com[0]*rot_index
                time.sleep(Convert.micros_to_sec(t))
                
                # Release gripper
                print("Releasing gripper")
                arduino.slave_command(["", "", "", "-1:0:0"])
                time.sleep(1)
                
            # Continue the search
            else:
                if Cx.value == 0 and Cy.value == 0:
                    # No object found, continue the search
                    if type(hardware_limit("rotation", 0)) == bool or rot_index < int(hardware_limit("rotation", 0)):
                        com = hardware_step("rotation", 0)
                        rot_com = f"{com[0]}:{round(com[1])}:{round(com[2])}"
                        arduino.slave_command(rot_com)
                        t = (com[1]+com[2])*com[0]*1
                        time.sleep(Convert.micros_to_sec(t))
                        rot_index += 1

                    else:
                        com = hardware_step("rotation", 0)
                        rot_com = f"-{com[0]*hardware_limit("rotation", 0)}:{round(com[1])}:{round(com[2])}"
                        arduino.slave_command(rot_com)
                        t = (com[1]+com[2])*com[0]*hardware_limit("rotation", 0)
                        time.sleep(Convert.micros_to_sec(t))
                        rot_index = 0
                else:
                    # Object in sight, but not alligned
                    # Rotate towards object
                    print("Object in sight")
                    com = hardware_step("rotation", 0)
                    if Cx.value <= imgCx:
                        rot_com = f"{com[0]}:{round(com[1])}:{round(com[2])}"
                        rot_index += 1
                    else:
                        rot_com = f"-{com[0]}:{round(com[1])}:{round(com[2])}"
                        rot_index -= 1
                        
                    t = (com[1]+com[2])*com[0]*1
                        
                    # Extend towards object
                    com = hardware_step("extend", 2)
                    if Cy.value <= imgCy:
                        ext_com = f"-{com[0]}:{round(com[1])}:{round(com[2])}"
                        extend_index -= 1
                    else:
                        ext_com = f"{com[0]}:{round(com[1])}:{round(com[2])}"
                        extend_index += 1
                        
                    t = max(t, com[0]*com[1])
                    
                    arduino.slave_command([rot_com, "", ext_com])
                    time.sleep(Convert.micros_to_sec(t))
                        
                            
            
        else:
            print("Manual Mode Active!")
        
        
        
        
        
        