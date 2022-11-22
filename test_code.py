import serial
import io
import sys
import RPi.GPIO as GPIO
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import numpy as np
import board
import adafruit_ssd1306
import displayio
from PIL import Image, ImageDraw, ImageFont


class Screen:

    def clear_window(self):
        splash = displayio.Group()
        self.display.show(splash)

    def draw_splash(self):
        print('Drawing splash...')
        splash = displayio.Group()
        
        color_bitmap = displayio.Bitmap(self.WIDTH, self.HEIGHT, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0xFFFFFF # White

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        splash.append(bg_sprite)

        inner_bitmap = displayio.Bitmap(self.WIDTH - 5  * 2, self.HEIGHT - 5 * 2, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000 # Black
        inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=5, y=5)

        splash.append(inner_sprite)

        self.display.show(splash)

    def hello_world(self):
        image = Image.new("1", (self.WIDTH, self.HEIGHT))
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), outline=255, fill=0)
        draw.rectangle((5, 5, self.WIDTH- 5 - 1, self.HEIGHT -5 - 1), outline=0, fill=0)

        font = ImageFont.load_default()

        text = "Hello world!"
        (font_width, font_height) = font.getsize(text)
        draw.text((self.WIDTH // 2 - font_width // 2, self.HEIGHT // 2 - font_height // 2), text, font=font, fill=255)

        # Display image
        self.display.image(image)
        self.display.show()

    def show_values(self, velocity, direction, step=None):

        self.current_draw_buffer.rectangle((0, 0, self.WIDTH, self.HEIGHT), outline=255, fill=0)
        #self.current_window, self.current_draw_buffer = self.draw_blank_window()
        direction_text = "Direction: {:}".format(self.direction_dict[direction])

        # Write direction
        (dir_font_width, dir_font_height) = self.font.getsize(direction_text)
        self.current_draw_buffer.text((2, 0), direction_text, font=self.font, fill=255)

        velocity_text = 'Speed: {:.1f} rpm'.format(velocity/self.MICROSTEP_RESOLUTION * 60)
        (vel_font_width, vel_font_height) = self.font.getsize(velocity_text)
        self.current_draw_buffer.text((2, dir_font_height-2), velocity_text, font=self.font, fill=255)

        step_text = "Step: {:}".format(step)
        (step_font_width, step_font_height) = self.font.getsize(step_text)
        self.current_draw_buffer.text((2, dir_font_height+vel_font_height-6), step_text, font=self.font, fill=255)

        self.display.image(self.current_window)
        self.display.show()


    def initialize_screen(self):

        image = Image.new("1", (self.WIDTH, self.HEIGHT))
        draw = ImageDraw.Draw(image)

        # Create black background
        draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), outline=255, fill=0)
        
        self.display.image(image)
        self.display.show()

        return image, draw

    def __init__(self):

        self.WIDTH = 128
        self.HEIGHT = 32
        self.MICROSTEP_RESOLUTION = 51200

        displayio.release_displays()
        self.i2c = board.I2C()
        #display_bus = displayio.I2CDisplay(self.i2c, device_address=0x3C)
   
        self.display = adafruit_ssd1306.SSD1306_I2C(self.WIDTH, self.HEIGHT, self.i2c)

        self.font = ImageFont.truetype('/usr/share/fonts/truetype/piboto/Piboto-Bold.ttf')

        self.direction_dict = {1: "---> FWD --->", -1: "<--- REV <---", 0: "--- STOP ---"}
        self.current_window, self.current_draw_buffer = self.initialize_screen()

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
        print('Input velocity is: {:}'.format(velocity))
        return self.execute('SL {:}\r'.format(velocity), output=output)

    def get_pot_voltage(self):
        try:
            volt = self.analog.voltage
            if volt < 0.001:
                volt = 0

        finally:
            return np.round(volt,3)
        
    def check_reset(self, channel):
        if GPIO.input(channel) == GPIO.HIGH:
            self.RESET_THIS_SHIT = True
            
        return self.RESET_THIS_SHIT    

    def set_leds(self):
        if self.speed_multiplier > 0:
            GPIO.output(self.led_reverse_channel, False)
            GPIO.output(self.led_forward_channel, True)
        elif self.speed_multiplier < 0:
            GPIO.output(self.led_forward_channel, False)
            GPIO.output(self.led_reverse_channel, True)

        else:
            GPIO.output(self.led_forward_channel, False)
            GPIO.output(self.led_reverse_channel, False)

    def get_direction(self):
        # Logic is:
        # Forward Reverse: FWD_CHAN REV_CHAN
        # F       F (switch off): Low Low
        # T       F (switch fwd): Low High
        # F       T (switch rev): High Low

        if self.forward_analog.voltage > 2.0 and self.reverse_analog.voltage < 2.0:
            if self.__capacitor_discharging:
                self.__capacitor_discharging = False
            multiplier = -1
        elif self.reverse_analog.voltage > 2.0 and self.forward_analog.voltage < 2.0:
            if self.__capacitor_discharging:
                self.__capacitor_discharging = False
            multiplier = 1
        else:
            multiplier = 0



        if self.forward_analog.voltage > 1.0 and self.reverse_analog.voltage > 1.0:
            if not self.__capacitor_discharging:
                multiplier = self.speed_multiplier * -1
                self.__capacitor_discharging = True
        
        self.speed_multiplier = multiplier

        self.set_leds()       
        return multiplier

    def voltage_to_speed(self,full_scale=3.3, scale='linear'):

        VOLT_MIN = 0.0
        SPEED_MIN = 0

        VOLT_MAX =  full_scale
        SPEED_MAX = 200000 # Resolution is 51200 steps/rev

        if scale == 'linear':
            voltage = self.get_pot_voltage()
            print('Pot voltage: {:}'.format(voltage))
            return self.get_direction()*int((SPEED_MAX-SPEED_MIN)/(VOLT_MAX-VOLT_MIN)*voltage)

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
    
    def read_position(self):
        return self.execute('PR P\r', output=True)
    
    def clear_position(self):
        return self.execute('P 0\r', output=True)

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
        
        self.__capacitor_discharging = False

        self.STEP_RESOLUTION = 51200

        # Initialize ADC for speed control
        self.adc_channels = {0: ADS.P0, 1: ADS.P1, 2: ADS.P2, 3: ADS.P3}
        # Velocity channel reads in potiometer output
        self.velocity_channel = 0
        # Forward and reverse are linked to a SPDT switch, need to specify logic once we figure it out
        self.forward_channel = 1
        self.reverse_channel = 2
        self.reset_channel = 3

        # Enable GPIO for LED control
        GPIO.setmode(GPIO.BCM)

        self.led_forward_channel = 24
        self.led_reverse_channel = 23
        self.reset_button_channel = 18

        GPIO.setup(self.led_forward_channel, GPIO.OUT)
        GPIO.setup(self.led_reverse_channel, GPIO.OUT)
        GPIO.setup(self.reset_button_channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        GPIO.add_event_detect(self.reset_button_channel, GPIO.RISING, callback=self.check_reset)
                                                                                                                                                                                                                                                                                
    
        # Create the I2C bus
        self.i2c_adc = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        self.adc = ADS.ADS1115(self.i2c_adc)

        # Create single-ended input on channel 0
        self.analog = AnalogIn(self.adc, self.adc_channels[self.velocity_channel])
        self.forward_analog = AnalogIn(self.adc, self.adc_channels[self.forward_channel])
        self.reverse_analog = AnalogIn(self.adc, self.adc_channels[self.reverse_channel])

        self.speed_multiplier = self.get_direction()
        self.__capacitor_discharging = False
        
        self.RESET_THIS_SHIT = False


if __name__ == '__main__':


    ronnie = Motor()
    screen = Screen()

    try:
        # Initialize screen
        
        while True:
            if ronnie.RESET_THIS_SHIT == True:
                print('Motor resetting...')
                ronnie.clear_position()
                # Code to reset motor position based on encoder steps
                ronnie.RESET_THIS_SHIT = False
                # I want 2 buttons -- one that sets the encoder step = 0 position, and one that resets motor to step = 0 position.
                
                
            velocity = ronnie.voltage_to_speed(scale='linear')
            pos = ronnie.read_position()[2]
            
            out = ronnie.set_velocity(velocity=velocity,output=True)
            screen.show_values(velocity, np.sign(velocity), step=pos)
            
            print('Forward voltage: {:.2f}; Reverse voltage: {:.2f}; Speed multiplier: {:}'.format(ronnie.forward_analog.voltage, ronnie.reverse_analog.voltage, ronnie.get_direction()))

    except: 
        ronnie.set_velocity(velocity=0, output=True)
        raise 
