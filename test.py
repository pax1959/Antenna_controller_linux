#test.py
import serial
print('Hello World!')
seriport=serial.Serial(port='/dev/ttyACM0',
                                      baudrate=9600,
                                      parity=serial.PARITY_NONE,
                                      stopbits=serial.STOPBITS_ONE,
                                      bytesize=serial.EIGHTBITS,
                                      timeout=5)