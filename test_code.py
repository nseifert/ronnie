import serial
import io
import sys
import RPi
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import numpy as np

class Motor:

    def execute(self, cmd: str, output=False):
        if self.isOpen():
            if '\n' not in cmd:
                cmd += '\n'
            print('command is: {:}'.format(cmd))
            self.connection.write(cmd)
            

            if output: 
                return self.flush_output()
            else:
                self.flush_output()   
                return True

        else: 
            return False 

    def set_velocity(self, velocity: int, output=False):
        return self.execute('SL {:}\r'.format(velocity), output=output)

    def get_pot_voltage(self):
        volt = self.analog.voltage
        if volt < 0.001:
            volt = 0
        return np.round(volt,3)


    def voltage_to_speed(self,full_scale=3.3, scale='linear'):

        VOLT_MIN = 0.0
        SPEED_MIN = 0

        VOLT_MAX =  full_scale
        SPEED_MAX = 200000 # Resolution is 51200 steps/rev

        if scale == 'linear':
            voltage = self.get_pot_voltage()
            print(voltage)
            return int((SPEED_MAX-SPEED_MIN)/(VOLT_MAX-VOLT_MIN)*voltage)

        if scale == 'log':
            # Does not work at the moment, need better function
            voltage = self.get_pot_voltage()

            # Convert speed = a*b^x + c
            y_m = 0.2
            b = (1/y_m - 1)**2
            print(voltage)
            return 0



    def read_velocity(self):
        return self.execute('PR V\r', output=True)    

    def self_identify(self):
        return self.execute('PR AL\r', output=True)

    def flush_output(self):
        self.connection.flush()
        output = []
        while True:
            temp = self.connection.read()
            output.append(temp)

            if not temp:
                break
        output = ''.join(output).split('\n')
        return output

    def close_connection(self):
        try:
            self.connection.close()
            return True
        except:
            raise 

    def isOpen(self):
        return self.raw_connection.is_open

    def __init__(self):

        # Initialize serial communication with motor
        self.addr = '/dev/ttyUSB0'
        self.baud = 9600
        self.timeout = 1/10.

        self.raw_connection = serial.Serial(self.addr, self.baud, timeout=self.timeout)
        self.connection = io.TextIOWrapper(io.BufferedRWPair(self.raw_connection, self.raw_connection))
        print('Connection to Ronnie is currently {:}'.format(self.isOpen()))

        self.STEP_RESOLUTION = 51200

        self.adc_channels = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
        self.channel = 0

        # Initialize ADC for speed control
        # Create the I2C bus
        self.i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        self.ads = ADS.ADS1115(self.i2c)

        # Create single-ended input on channel 0
        self.analog = AnalogIn(self.ads, self.adc_channels[self.channel])


if __name__ == '__main__':


    ronnie = Motor()
    try:
        while True:
            #ronnie.set_velocity(velocity=0)
            out = ronnie.set_velocity(velocity=ronnie.voltage_to_speed(scale='linear'),output=True)

    except: 
        ronnie.set_velocity(velocity=0, output=True)
        raise 
