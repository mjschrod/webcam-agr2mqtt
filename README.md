# webcam-agr2mqtt

Reads an analog gauge on a webcam and provides result via mqtt

Still in development / testing

The mqtt-processes are programmed not very sophisticated:
After transmission of the measured/calculated values there is a hard disconnect from the mqtt-broker.
So, the connection will again be initiated at every measurement.
