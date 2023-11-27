FROM python:3.10

RUN apt-get update
RUN apt install -y libgl1-mesa-glx

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV MIN_ANGLE=0
ENV MAX_ANGLE=360
ENV MIN_VALUE=0
ENV MAX_VALUE=100
ENV UNITS="a-unit"

ENV READINGS=5
ENV PAUSE_BTWN_READINGS=1.5
ENV PAUSE_BTWN_MEASUREMENTS=10
ENV CAMERA_LIGHTNING=2

ENV SEND_SINGLE_READINGS="yes"
ENV SEND_MEAN_READINGS="yes"

ENV MQTT_IP="192.168.0.2"
ENV MQTT_PORT="1883"
ENV MQTT_USER="mqtt-user"
ENV MQTT_PASS="mqtt-password"
ENV MQTT_CLIENTID="MQTT-Analog-Gauge-Reader"
ENV MQTT_TOPIC_SINGLE="gauge_1_single"
ENV MQTT_TOPIC_MEAN="gauge_1_mean"

ENV WEBCAM_IP="192.168.0.3"
ENV WEBCAM_PATH="/snapshot.jpg"
ENV WEBCAM_PATH_LED_ON="/cm?cmnd=Power%20ON"
ENV WEBCAM_PATH_LED_OFF="/cm?cmnd=Power%20OFF"

ADD main.py .

CMD ["python", "main.py"]

