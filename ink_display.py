# TODO: Merge into epd7 lib
import sys
import os
import logging.config
from lib import epd7in3f
import time
import json
from PIL import Image, ImageDraw, ImageFont

IMG_DIR = "assets/images"
FONT_DIR = "assets/fonts"
LIB_DIR = "lib/"
LOGGER = logging.getLogger(__name__)

file_path = os.path.abspath(__file__)
cwd = os.path.dirname(file_path)
config_file = f"{cwd}/logging.json"
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


class InkDisplay:
    def __init__(self) -> None:
        self.ink = epd7in3f.EPD()
        self.draw_image = self.blank_image()
        self.width = 800
        self.height = 480
        self.center = (self.width // 2, self.height // 2)
        self.is_clear = False

    def init(self) -> None:
        LOGGER.info("initialising")
        if os.path.exists(LIB_DIR):
            sys.path.append(LIB_DIR)
        self.ink.init()

    def clear(self, force=False) -> None:
        LOGGER.info("clearing screen")
        if self.is_clear and not force:
            return
        try:
            self.ink.Clear()
            self.is_clear = True
        except Exception as e:
            f"Unexpected error while trying to clear screen: {e}"

    def sleep(self) -> None:
        LOGGER.info("putting to sleep")
        self.ink.sleep()

    def exit(self) -> None:
        LOGGER.info("ctrl + c:")
        epd7in3f.epdconfig.module_exit()

    def display_image(self, image) -> None:
        self.is_clear = False
        LOGGER.info("displaying image")
        Himage = Image.open(os.path.join(IMG_DIR, image))
        self.ink.display(self.ink.getbuffer(Himage))

    def blank_image(self) -> Image:
        LOGGER.info("creating new draw image")
        return Image.new("RGB", (self.ink.width, self.ink.height), self.ink.WHITE)

    def draw(self, image) -> ImageDraw:
        return ImageDraw.Draw(image)

    def draw_text(self, location, text, font, size, color, draw) -> None:
        self.is_clear = False
        LOGGER.info("drawing text to draw image: %s", text)
        draw.text(
            (location),
            text=text,
            font=ImageFont.truetype(os.path.join(FONT_DIR, font), size),
            fill=color,
        )

    def display_draw(self, image) -> None:
        self.is_clear = False
        LOGGER.info("displaying draw image")
        self.ink.display(self.ink.getbuffer(image))

    def convert_24bmp(self, image_path, output_path=False):
        try:
            img = Image.open(image_path)
            img = img.convert("RGB")
            if output_path is False:
                img.save(image_path, "BMP")
            else:
                img.save(output_path, "BMP")
        except FileNotFoundError:
            LOGGER.error(f"Image file not found at {image_path}")
        except Exception as e:
            LOGGER.error(f"Unhandled error: {e}")
