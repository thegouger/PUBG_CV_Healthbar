# image processing / support stuff
import numpy as np
from PIL import ImageGrab
from PIL import Image
import cv2
from time import sleep
import os
import json
from collections import deque

# http server
from http.server import *
from threading import Thread

# health percentage global
health_percentage = 100

## config data
try:
    with open('config.json') as config_file:
        config_data = json.load(config_file)
except:
    config_data = {
                     'SERVER_PORT': 6969,
                     'GAME_WIDTH': 1920,
                     'GAME_HEIGHT': 1080,
                     'CUSTOM_HTML': False
                  }
    with open('config.json', 'w') as config_file:
        json.dump(config_data, config_file)

print(config_data)
SERVER_PORT = config_data['SERVER_PORT']
GAME_WIDTH  = config_data['GAME_WIDTH']
GAME_HEIGHT = config_data['GAME_HEIGHT']
CUSTOM_HTML = config_data['CUSTOM_HTML']

## support for pyinstaller
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """

    if(CUSTOM_HTML):
        base_path = os.path.abspath(".")
    else:
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

## http server
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if(self.path == "/health"): # health endpoint (that js will continuously request)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes('{\"health\":' + str(health_percentage) + '}', 'utf-8'))
        elif('images' in self.path): # serve gifs
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            image_name = self.path.split('images/', 1)[1]
            image = open(resource_path('images/' + image_name), 'rb')
            self.wfile.write(image.read())
            image.close()
        else: # serve main html
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = open(resource_path('index.html'), 'rb')
            self.wfile.write(html.read())

def server_run():
    server_address = ('', SERVER_PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()

server_thread = Thread(target=server_run)
server_thread.setDaemon = True
server_thread.start()

## healthbar detection
frame_ring_buffer = deque([], 3)
while(True):
    top_left     = (GAME_WIDTH * 0.3974, GAME_HEIGHT * 0.95)
    bottom_right = (GAME_WIDTH * 0.601, GAME_HEIGHT * 0.972)
    healthbar_width = GAME_WIDTH * (0.601 - 0.3974)

    # grab healthbar
    screengrab = ImageGrab.grab((top_left[0], top_left[1], bottom_right[0], bottom_right[1]))
    frame_ring_buffer.append(screengrab)

    # maintain ring buffer of grabs and pick max values (to eliminate problems from flashing health bar)
    frame1 = cv2.cvtColor(np.array(frame_ring_buffer[0]), cv2.COLOR_RGB2BGR)
    if(len(frame_ring_buffer) == 3):
        frame2 = cv2.cvtColor(np.array(frame_ring_buffer[1]), cv2.COLOR_RGB2BGR)
        frame3 = cv2.cvtColor(np.array(frame_ring_buffer[2]), cv2.COLOR_RGB2BGR)
        frame2 = cv2.max(frame1, frame2)
        health_bar = cv2.max(frame2, frame3)
    else:
        health_bar = frame1
    
    # mask out non red-white pixels and threshold health bar
    health_bar = cv2.bilateralFilter(health_bar, 3, 80, 80)
    mask1 = cv2.inRange(health_bar, np.array([0, 0, 170]), np.array([255, 255, 255]))

    # get mask of 'red' by hsv conversion (bar is deep red when health is very low)
    health_bar_hsv = cv2.cvtColor(health_bar, cv2.COLOR_BGR2HSV)
    
    lower_red1 = np.array([170, 110, 85])
    upper_red1 = np.array([180, 255, 255])
    lower_red2 = np.array([0, 110, 85])
    upper_red2 = np.array([10, 255, 255])
    
    mask2 = cv2.inRange(health_bar_hsv, lower_red1, upper_red1)
    mask3 = cv2.inRange(health_bar_hsv, lower_red2, upper_red2)
    hsvBar = cv2.bitwise_or(mask2, mask3)
         
    health_bar = cv2.bitwise_and(health_bar, health_bar, mask = mask1)
    health_bar = cv2.cvtColor(health_bar, cv2.COLOR_BGR2GRAY)
    ret,health_bar_thresh = cv2.threshold(health_bar,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # get health rectangle (contour with leftmost left boundary)
    _, contoursRedWhite, _ = cv2.findContours(health_bar_thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    _, contoursRed, _      = cv2.findContours(hsvBar,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    lowMinX = minX = bottom_right[0] + 10
    for contour in contoursRedWhite:
        x,y,w,h = cv2.boundingRect(contour)
        if(x < minX):
            healthContour = contour
            minX = x
            
    for contour in contoursRed:
        x,y,w,h = cv2.boundingRect(contour)
        if(x < lowMinX):
            lowHealthContour = contour
            lowMinX = x

    # try to use a contour from the 'red-white' image
    redWhiteContourFound = False
    try:
        if (minX > 5): # in the event that we found a contour that doesn't touch the left edge, we ignore it
            health_percentage = 100
        else:
            health_percentage = healthContour[3][0][0] / healthbar_width * 100
            redWhiteContourFound = True
    except:
        pass

    # otherwise use a contour from the 'deep red' image
    if(not redWhiteContourFound):
        try:
            if (lowMinX > 5): # in the event that we found a contour that doesn't touch the left edge, we ignore it
                health_percentage = 100
            else:
                health_percentage = lowHealthContour[3][0][0] / healthbar_width * 100
        except:
           pass

    print('Detected health ' + str(health_percentage))
    sleep(0.5)
