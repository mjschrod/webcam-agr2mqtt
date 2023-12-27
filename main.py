# Python program to read analog gauge from camera ESP 32CAM
# And send the result to MQTT broker
  																																																
import numpy as np
import cv2
import time
from urllib.request import urlopen
#import json
import paho.mqtt.client as mqtt
import requests
import os

min_angle = float(os.environ['MIN_ANGLE'])
max_angle = float(os.environ['MAX_ANGLE'])
min_value = float(os.environ['MIN_VALUE'])
max_value = float(os.environ['MAX_VALUE'])
units = os.environ['UNITS']
print (min_angle, max_angle, min_value, max_value)

actualreading = 1
readings = int(os.environ['READINGS'])
pause_btwn_readings = float(os.environ['PAUSE_BTWN_READINGS'])
pause_btwn_measurements = float(os.environ['PAUSE_BTWN_MEASUREMENTS'])
camera_lightning = float(os.environ['CAMERA_LIGHTNING'])

#readings = int(readings)
#pause_btwn_readings = float(pause_btwn_readings)
#pause_btwn_measurements = float(pause_btwn_measurements)
#camera_lightning = float(pause_btwn_measurements)

SEND_SINGLE_READINGS = os.environ['SEND_SINGLE_READINGS']
SEND_MEAN_READINGS = os.environ['SEND_MEAN_READINGS']

MQTT_IP = os.environ['MQTT_IP']
MQTT_PORT = int(os.environ['MQTT_PORT'])
MQTT_USER = os.environ['MQTT_USER']
MQTT_PASS = os.environ['MQTT_PASS']
MQTT_CLIENTID = os.environ['MQTT_CLIENTID']

MQTT_TOPIC_SINGLE = os.environ['MQTT_TOPIC_SINGLE']
MQTT_TOPIC_MEAN = os.environ['MQTT_TOPIC_MEAN']

WEBCAM_IP = os.environ['WEBCAM_IP']
WEBCAM_PATH = os.environ['WEBCAM_PATH']
WEBCAM_PATH_LED_ON = os.environ['WEBCAM_PATH_LED_ON']
WEBCAM_PATH_LED_OFF = os.environ['WEBCAM_PATH_LED_OFF']

messwerte =[]

print("This program will recognize gauge meter value from camera, please aim the camera to gauge!")
print("Initial parameter of gauge:")

#Change this value based on ESP32 Cam IP address
#url = r'http://192.168.0.x:80/snapshot.jpg'
url = r'http://' + WEBCAM_IP + WEBCAM_PATH
urlon = r'http://' + WEBCAM_IP + WEBCAM_PATH_LED_ON
urloff = r'http://' + WEBCAM_IP + WEBCAM_PATH_LED_OFF

print (url)
print (urlon)
print (urloff)
print (MQTT_IP)
print (MQTT_PORT)

val = 0
val_before = 0

#For MQTT connection
def on_connect(client, userdata, flags, rc):
	if rc == 0:
		print("Connected successfully")
	else:
		print("Connect returned result code: " + str(rc))

#For image recognition
def avg_circles(circles, b):
    avg_x=0
    avg_y=0
    avg_r=0
    for i in range(b):
        #optional - average for multiple circles (can happen when a gauge is at a slight angle)
        avg_x = avg_x + circles[0][i][0]
        avg_y = avg_y + circles[0][i][1]
        avg_r = avg_r + circles[0][i][2]
    avg_x = int(avg_x/(b))
    avg_y = int(avg_y/(b))
    avg_r = int(avg_r/(b))
    return avg_x, avg_y, avg_r

def dist_2_pts(x1, y1, x2, y2):
    #print np.sqrt((x2-x1)^2+(y2-y1)^2)
	return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

requests.get(urlon)
time.sleep (camera_lightning)

while actualreading < (int(readings) + int(666)):

    try:
        if actualreading < (int (readings) + int(1)):
            #requests.get("urlon")
#while True:
            img_resp = urlopen(url)
            imgnp = np.asarray(bytearray(img_resp.read()), dtype="uint8")
            #ret, img = cv2.imdecode(imgnp, -1)																																																																																																																																		
            img = cv2.imdecode(imgnp, -1)
            #cv2.imshow('Analog Gauge Reader', img)

		#calibrate function
		#======================================================================================
            img_blur = cv2.GaussianBlur(img, (5,5), 3)
            gray = cv2.cvtColor(img_blur, cv2.COLOR_BGR2GRAY)  #convert to gray        
            height, width = img.shape[:2]
		
		#restricting the search from 35-48% of the possible radii gives fairly good results across different samples.  Remember that
		#these are pixel values which correspond to the possible radii search range.
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, np.array([]), 100, 50, int(height*0.35), int(height*0.48))
		# average found circles, found it to be more accurate than trying to tune HoughCircles parameters to get just the right one
            a, b, c = circles.shape
            x,y,r = avg_circles(circles, b)

		#draw center and circle
            cv2.circle(img, (x, y), r, (0, 0, 255), 3, cv2.LINE_AA)  # draw circle
            cv2.circle(img, (x, y), 2, (0, 255, 0), 3, cv2.LINE_AA)  # draw center of circle

            separation = 10.0 #in degrees
            interval = int(360 / separation)
            p1 = np.zeros((interval,2))  #set empty arrays
            p2 = np.zeros((interval,2))
            p_text = np.zeros((interval,2))
            for i in range(0,interval):
                for j in range(0,2):
                    if (j%2==0):
                        p1[i][j] = x + 0.9 * r * np.cos(separation * i * 3.14 / 180) #point for lines
                    else:
                        p1[i][j] = y + 0.9 * r * np.sin(separation * i * 3.14 / 180)
            text_offset_x = 10
            text_offset_y = 5
            for i in range(0, interval):
                for j in range(0, 2):
                    if (j % 2 == 0):
                        p2[i][j] = x + r * np.cos(separation * i * 3.14 / 180)
                        p_text[i][j] = x - text_offset_x + 1.2 * r * np.cos((separation) * (i+9) * 3.14 / 180) #point for text labels, i+9 rotates the labels by 90 degrees
                    else:
                        p2[i][j] = y + r * np.sin(separation * i * 3.14 / 180)
                        p_text[i][j] = y + text_offset_y + 1.2* r * np.sin((separation) * (i+9) * 3.14 / 180)  # point for text labels, i+9 rotates the labels by 90 degrees

		#add the lines and labels to the image
            for i in range(0,interval):
                cv2.line(img, (int(p1[i][0]), int(p1[i][1])), (int(p2[i][0]), int(p2[i][1])),(0, 255, 0), 2)
                cv2.putText(img, '%s' %(int(i*separation)), (int(p_text[i][0]), int(p_text[i][1])), cv2.FONT_HERSHEY_SIMPLEX, 0.3,(0,0,0),1,cv2.LINE_AA)
		
		#======================================================================================	
		#//////////////////////////////////////////////////////////////////////////////////////
            gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

		# Set threshold and maxValue
            thresh = 175
            maxValue = 255

		# apply thresholding which helps for finding lines
            th, dst2 = cv2.threshold(gray2, thresh, maxValue, cv2.THRESH_BINARY_INV);

		# find lines
            minLineLength = 10
            maxLineGap = 0
            lines = cv2.HoughLinesP(image=dst2, rho=3, theta=np.pi / 180, threshold=100,minLineLength=minLineLength, maxLineGap=0)  # rho is set to 3 to detect more lines, easier to get more then filter them out later

		# remove all lines outside a given radius
            final_line_list = []
		#print "radius: %s" %r

            diff1LowerBound = 0.15 #diff1LowerBound and diff1UpperBound determine how close the line should be from the center
            diff1UpperBound = 0.25
            diff2LowerBound = 0.5 #diff2LowerBound and diff2UpperBound determine how close the other point of the line should be to the outside of the gauge
            diff2UpperBound = 1.0
            for i in range(0, len(lines)):
                for x1, y1, x2, y2 in lines[i]:
                    diff1 = dist_2_pts(x, y, x1, y1)  # x, y is center of circle
                    diff2 = dist_2_pts(x, y, x2, y2)  # x, y is center of circle
				#set diff1 to be the smaller (closest to the center) of the two), makes the math easier
                    if (diff1 > diff2):
                        temp = diff1
                        diff1 = diff2
                        diff2 = temp
				# check if line is within an acceptable range
                    if (((diff1<diff1UpperBound*r) and (diff1>diff1LowerBound*r) and (diff2<diff2UpperBound*r)) and (diff2>diff2LowerBound*r)):
                        line_length = dist_2_pts(x1, y1, x2, y2)
					# add to final list
                        final_line_list.append([x1, y1, x2, y2])

		# assumes the first line is the best one
            x1 = final_line_list[0][0]
            y1 = final_line_list[0][1]
            x2 = final_line_list[0][2]
            y2 = final_line_list[0][3]
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

		#for testing purposes, show the line overlayed on the original image
		#cv2.imwrite(folder_path + "/" + filename + "-needle.jpg", img)

		#find the farthest point from the center to be what is used to determine the angle
            dist_pt_0 = dist_2_pts(x, y, x1, y1)
            dist_pt_1 = dist_2_pts(x, y, x2, y2)
            if (dist_pt_0 > dist_pt_1):
                x_angle = x1 - x
                y_angle = y - y1
            else:
                x_angle = x2 - x
                y_angle = y - y2
		# take the arc tan of y/x to find the angle
            res = np.arctan(np.divide(float(y_angle), float(x_angle)))
		#np.rad2deg(res) #coverts to degrees

		# print x_angle
		# print y_angle
		# print res
		# print np.rad2deg(res)

		#these were determined by trial and error
            res = np.rad2deg(res)
            if x_angle > 0 and y_angle > 0:  #in quadrant I
                final_angle = 270 - res
            if x_angle < 0 and y_angle > 0:  #in quadrant II
                final_angle = 90 - res
            if x_angle < 0 and y_angle < 0:  #in quadrant III
                final_angle = 90 - res
            if x_angle > 0 and y_angle < 0:  #in quadrant IV
                final_angle = 270 - res

		#print final_angle

            old_min = float(min_angle)
            old_max = float(max_angle)

            new_min = float(min_value)
            new_max = float(max_value)

            old_value = final_angle

            old_range = (old_max - old_min)
            new_range = (new_max - new_min)
            new_value = (((old_value - old_min) * new_range) / old_range) + new_min
		
		#//////////////////////////////////////////////////////////////////////////////////////
            val = new_value
            #print ("Current reading: %s %s" %(("%.2f" % val), units))
		

		
		#Start to send MQTT==========================================================
            if (val>0 and SEND_SINGLE_READINGS=='yes'):
                value_sent = ("%.2f" % val)
                client_id = MQTT_CLIENTID
                client = mqtt.Client(client_id)
                if client.is_connected() == False:
                    client.on_connect = on_connect
			# enable TLS
			#client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
			# set username and password
                    client.username_pw_set(MQTT_USER, MQTT_PASS)

			# connect to MQTT broker, set the broker and port
                    client.connect(MQTT_IP, MQTT_PORT)
                client.publish(MQTT_TOPIC_SINGLE, value_sent)
                client.loop_start()
            time.sleep(pause_btwn_readings)
		#1.5 sec zuvor
		#interupt
            if cv2.waitKey(30) & 0xff == ord('q'):
                break
            print (actualreading)
            actualreading = actualreading + 1
            print ("Current reading: %s %s" %(("%.2f" % val), units))
            messwerte.append(val)
            meanvalue = np.mean(messwerte)
            print("Meanvalue is ", meanvalue)


        else:
            if (meanvalue>0 and SEND_MEAN_READINGS=='yes'):
                meanvalue_sent = ("%.2f" % meanvalue)
                #client_id = 'MQTT2_oilcamanalyzer.1'
                client_id = MQTT_CLIENTID
                client = mqtt.Client(client_id)
                if client.is_connected() == False:
                    client.on_connect = on_connect
			# enable TLS
			#client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
			# set username and password
                client.username_pw_set(MQTT_USER, MQTT_PASS)

			# connect to MQTT broker, set the broker and port
                client.connect(MQTT_IP, MQTT_PORT)
                client.publish(MQTT_TOPIC_MEAN, meanvalue_sent)
                client.loop_start()
            
            requests.get(urloff)
            print ("pause")
            messwerte.clear()
            print ("Messwerte gelöscht")
            print(messwerte)
            #Nächste Zeile ist neu:
            client.disconnect(client)
            time.sleep (pause_btwn_measurements)
            actualreading = 1
            requests.get(urlon)
            time.sleep (camera_lightning)

    except ValueError as ve:
        print('Error read the image!!')
        x = "do nothing"
    except IndexError:
        print('Error calculate the value!!')
        x = "do nothing"
        