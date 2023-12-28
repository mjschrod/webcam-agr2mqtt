# webcam-agr2mqtt

Reads an analog gauge on a webcam and provides result via mqtt.
The defaults are adapted to the pathes of a tasmota esp32cam.

Still in development / testing

The mqtt-processes are programmed not very sophisticated:
After transmission of the measured/calculated values there is a hard disconnect from the mqtt-broker.
So, the connection will again be initiated at every measurement.



# Installation


## A) Get the Sources
git clone https://github.com/mjschrod/webcam-agr2mqtt 

$ cd webcam-agr2mqtt


## B) Build the installation image

$ sudo docker build -t webcam-agr2mqtt:0.4 .


## C) Edit docker-compose.yaml to your needs


## D) Install and Start the Docker-Container or if only changes were made in docker-compose.yaml recreate the container

$ sudo docker compose up -d --force-recreate
