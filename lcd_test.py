import adafruit_ssd1306
import displayio
import board
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time

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
        



def main():
    screen = Screen()
    

    encoder_step = 0
    while True:
            direction = np.random.choice([-1, 0, 1])
            velocity = np.random.randint(0, 250000) * direction

            encoder_step += velocity

            screen.show_values(velocity,direction, encoder_step)
            time.sleep(1/15)

if __name__ == "__main__":
    main()
