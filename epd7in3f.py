import logging.config
from . import epdconfig
import PIL
from PIL import Image
import io
import json
import os

# Display resolution
EPD_WIDTH = 800
EPD_HEIGHT = 480

logger = logging.getLogger(__name__)
file_path = os.path.abspath(__file__)
cwd = os.path.dirname(file_path)
config_file = f"{cwd}/../logging.json"
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.ratio = self.height / self.width
        self.BLACK = 0x000000  # 0000  BGR
        self.WHITE = 0xFFFFFF  # 0001
        self.GREEN = 0x00FF00  # 0010
        self.BLUE = 0xFF0000  # 0011
        self.RED = 0x0000FF  # 0100
        self.YELLOW = 0x00FFFF  # 0101
        self.ORANGE = 0x0080FF  # 0110

    # Hardware reset
    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)
        epdconfig.digital_write(self.reset_pin, 0)  # module reset
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    # send a lot of data
    def send_data2(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)

    def ReadBusyH(self):
        logger.debug("e-Paper busy H")
        while epdconfig.digital_read(self.busy_pin) == 0:  # 0: busy, 1: idle
            epdconfig.delay_ms(5)
        logger.debug("e-Paper busy H release")

    def TurnOnDisplay(self):
        self.send_command(0x04)  # POWER_ON
        self.ReadBusyH()

        self.send_command(0x12)  # DISPLAY_REFRESH
        self.send_data(0x00)
        self.ReadBusyH()

        self.send_command(0x02)  # POWER_OFF
        self.send_data(0x00)
        self.ReadBusyH()

    def init(self):
        if epdconfig.module_init() != 0:
            return -1
        # EPD hardware init start
        self.reset()
        self.ReadBusyH()
        epdconfig.delay_ms(30)

        self.send_command(0xAA)  # CMDH
        self.send_data(0x49)
        self.send_data(0x55)
        self.send_data(0x20)
        self.send_data(0x08)
        self.send_data(0x09)
        self.send_data(0x18)

        self.send_command(0x01)
        self.send_data(0x3F)
        self.send_data(0x00)
        self.send_data(0x32)
        self.send_data(0x2A)
        self.send_data(0x0E)
        self.send_data(0x2A)

        self.send_command(0x00)
        self.send_data(0x5F)
        self.send_data(0x69)

        self.send_command(0x03)
        self.send_data(0x00)
        self.send_data(0x54)
        self.send_data(0x00)
        self.send_data(0x44)

        self.send_command(0x05)
        self.send_data(0x40)
        self.send_data(0x1F)
        self.send_data(0x1F)
        self.send_data(0x2C)

        self.send_command(0x06)
        self.send_data(0x6F)
        self.send_data(0x1F)
        self.send_data(0x1F)
        self.send_data(0x22)

        self.send_command(0x08)
        self.send_data(0x6F)
        self.send_data(0x1F)
        self.send_data(0x1F)
        self.send_data(0x22)

        self.send_command(0x13)  # IPC
        self.send_data(0x00)
        self.send_data(0x04)

        self.send_command(0x30)
        self.send_data(0x3C)

        self.send_command(0x41)  # TSE
        self.send_data(0x00)

        self.send_command(0x50)
        self.send_data(0x3F)

        self.send_command(0x60)
        self.send_data(0x02)
        self.send_data(0x00)

        self.send_command(0x61)
        self.send_data(0x03)
        self.send_data(0x20)
        self.send_data(0x01)
        self.send_data(0xE0)

        self.send_command(0x82)
        self.send_data(0x1E)

        self.send_command(0x84)
        self.send_data(0x00)

        self.send_command(0x86)  # AGID
        self.send_data(0x00)

        self.send_command(0xE3)
        self.send_data(0x2F)

        self.send_command(0xE0)  # CCSET
        self.send_data(0x00)

        self.send_command(0xE6)  # TSSET
        self.send_data(0x00)
        return 0

    def crop_image(self, image, width, height):
        conversion_width = height / (self.height / self.width) // 1
        width_diff = width - conversion_width
        cut = width_diff // 2
        box = (cut, 0, conversion_width, height)
        print(f"{box=}")
        cropped_image = image.crop(box)
        print("cropped image size: ", cropped_image.size)
        return cropped_image

    def getbuffer(self, image):
        # Create a pallette with the 7 colors supported by the panel
        pal_image = Image.new("P", (1, 1))
        pal_image.putpalette(
            (
                0,
                0,
                0,
                255,
                255,
                255,
                0,
                255,
                0,
                0,
                0,
                255,
                255,
                0,
                0,
                255,
                255,
                0,
                255,
                128,
                0,
            )
            + (0, 0, 0) * 249
        )

        # Check if we need to rotate the image
        imwidth, imheight = image.size
        imratio = imheight / imwidth
        image_temp = image
        if imwidth == self.width and imheight == self.height:
            image_temp = image
        if imwidth <= self.height and imheight >= self.width:
            image_temp = image.rotate(90, expand=True)
        if imratio != self.ratio:
            print("cropping")
            image_temp = self.crop_image(image_temp, imwidth, imheight)
            print("cropped: ", image_temp.size)
        image_temp = image_temp.resize(
            (self.width, self.height), Image.Resampling.LANCZOS
        )
        # Convert the source image to the 7 colors, dithering if needed
        image_7color = image_temp.convert("RGB").quantize(palette=pal_image)
        buf_7color = bytearray(image_7color.tobytes("raw"))

        # PIL does not support 4 bit color, so pack the 4 bits of color
        # into a single byte to transfer to the panel
        buf = [0x00] * int(self.width * self.height / 2)
        idx = 0
        for i in range(0, len(buf_7color), 2):
            buf[idx] = (buf_7color[i] << 4) + buf_7color[i + 1]
            idx += 1

        return buf

    def display(self, image):
        self.send_command(0x10)
        self.send_data2(image)

        self.TurnOnDisplay()

    def Clear(self, color=0x11):
        self.send_command(0x10)
        self.send_data2([color] * int(self.height) * int(self.width / 2))

        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x07)  # DEEP_SLEEP
        self.send_data(0xA5)

        epdconfig.delay_ms(2000)
        epdconfig.module_exit()


### END OF FILE ###
