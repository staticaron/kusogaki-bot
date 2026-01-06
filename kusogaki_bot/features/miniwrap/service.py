import colorsys
import json
import logging
from io import BytesIO
from string import Template

import aiohttp
import requests
from PIL import Image, ImageDraw, ImageFont

import kusogaki_bot.shared.utils.colors as colors
from kusogaki_bot.features.miniwrap.fetch_data import (
    UserData,
    fetch_user_data,
)

logger = logging.getLogger(__name__)

IMG_WIDTH = 1324
IMG_HEIGHT = 303

COLORS = {
    'bg': '#0B1622',
    'dull': '#152232',
    'bdull': '#243A56',
    'fg': '#FFFFFF',
    'hl': '#D777CA',
}

FONT_LOCATION = {
    'inpin': 'static/fonts/inpin.ttf',
    'overpass-semibold': 'static/fonts/overpass-semibold.ttf',
    'overpass-extrabold': 'static/fonts/overpass-extrabold.ttf',
}

WRAP_BACKGROUND = 'static/wrap_background.png'
NO_DATA_IMG = 'static/nodata.png'

ELEMENTS_FILE_LOCATION = 'kusogaki_bot/features/miniwrap/data/elements.json'
ANCHORS_FILE_LOCATION = 'kusogaki_bot/features/miniwrap/data/anchors.json'


class GenerationResponse:
    def __init__(self, success: bool = True, error_msg: str = '', username=''):
        self.success = success
        self.error_msg = error_msg
        self.image_bytes = bytes()
        self.username = username


class AniWrapService:
    def __init__(self):
        self.load_data_into_templates()

        self.no_data_img = Image.open(NO_DATA_IMG)
        self.background_img = Image.open(WRAP_BACKGROUND)

    def load_data_into_templates(self):
        """Read the elements.json and anchors.json files and creates Templates"""

        with open(ELEMENTS_FILE_LOCATION, 'r') as element_fin:
            element_data_raw = element_fin.read()
            self.element_template = Template(element_data_raw)

        with open(ANCHORS_FILE_LOCATION, 'r') as anchors_fin:
            anchor_data_raw = anchors_fin.read()
            self.anchor_template = Template(anchor_data_raw)

    async def get_font(self, type: str, font_size: int):
        return ImageFont.truetype(FONT_LOCATION[type], font_size)

    async def center_anchor_point(
        self, available_space: int, element_width: int
    ) -> int:
        return int(available_space * 0.5 - element_width * 0.5)

    async def render_text(
        self,
        drawLayer: ImageDraw.ImageDraw,
        anchor_data: dict,
        element_data: dict,
        text_data: dict,
        color: str = '#ffffff',
    ) -> dict:
        """Fetch the data from the data container"""
        font_size = text_data['size']
        font_name = text_data['font']
        text = text_data['text']
        x_offset = text_data['x_offset']
        y_offset = text_data['y_offset']
        anchor = text_data.get('anchor', 'main_anchor')
        after = text_data.get('after', '')

        """Calculate the text Width and Height and save it in the data container"""
        font = await self.get_font(font_name, font_size)
        font_bbox = font.getbbox(text)

        text_data['width'] = int(font_bbox[2] - font_bbox[0])
        text_data['height'] = int(font_bbox[3] - font_bbox[1])

        """If offset is null, center the element"""
        if x_offset is None:
            x_offset = -text_data['width'] * 0.5

        if y_offset is None:
            y_offset = -text_data['height'] * 0.5

        """If there is not after element, draw according to the anchor, otherwise render after the after element"""
        if after == '':
            text_data['x_pos'] = anchor_data[anchor]['x'] + x_offset
            text_data['y_pos'] = anchor_data[anchor]['y'] + y_offset
        else:
            text_data['x_pos'] = (
                element_data[after]['x_pos'] + element_data[after]['width']
            )
            text_data['y_pos'] = element_data[after]['y_pos']

        drawLayer.text(
            (text_data['x_pos'], text_data['y_pos']),
            text,
            fill=color,
            font=font,
            features=['-kern'],
        )

        return text_data

    async def render_text_right(
        self,
        drawLayer: ImageDraw.ImageDraw,
        anchor_data: dict,
        element_data: dict,
        text_data: dict,
        color: str = '#ffffff',
    ) -> dict:
        """Fetch the data from the data container"""
        font_size = text_data['size']
        font_name = text_data['font']
        text = text_data['text']
        x_offset = text_data['x_offset']
        y_offset = text_data['y_offset']
        anchor = text_data.get('anchor', 'main_anchor')
        after = text_data.get('after', '')

        """Calculate the text Width and Height and save it in the data container"""
        font = await self.get_font(font_name, font_size)
        font_bbox = font.getbbox(text)

        text_data['width'] = int(font_bbox[2] - font_bbox[0])
        text_data['height'] = int(font_bbox[3] - font_bbox[1])

        if after == '':
            text_data['x_pos'] = (
                anchor_data[anchor]['x'] - x_offset - text_data['width']
            )
            text_data['y_pos'] = anchor_data[anchor]['y'] + y_offset
        else:
            text_data['x_pos'] = (
                element_data[after]['x_pos'] - x_offset - text_data['width']
            )
            text_data['y_pos'] = element_data[after]['y_pos']

        drawLayer.text(
            (text_data['x_pos'], text_data['y_pos']),
            text,
            fill=color,
            font=font,
            features=['-kern'],
        )

        return text_data

    async def apply_rounded_corners(
        self, image: Image.Image, width: int, height: int, radius: int
    ) -> Image.Image:
        mask = Image.new('L', (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            (0, 0, width, height),
            radius,
            fill='white',
        )

        image.putalpha(mask)

        return image

    async def create_colored_image(
        self, width: int, height: int, color_rgb
    ) -> Image.Image:
        overlay = Image.new('RGBA', [width, height], color_rgb + (255,))
        return overlay

    async def render_image(
        self,
        drawImage: Image.Image,
        url: str,
        anchor_data: dict,
        element_data: dict,
        image_data: dict,
    ) -> None:
        x_offset = image_data['x_offset']
        y_offset = image_data['y_offset']
        width = image_data['width']
        height = image_data['height']
        anchor = image_data.get('anchor', 'main_anchor')

        if url != '':
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as image_response:
                    image_bytes = await image_response.read()
                    image: Image.Image = Image.open(BytesIO(image_bytes))
        else:
            # Get the HSV primary color, increase brightness component a bit, and create basic image to represent lack of image
            col = colorsys.rgb_to_hsv(
                self.primary_color[0], self.primary_color[1], self.primary_color[2]
            )
            dampen_col_hsv = (col[0], col[1], min(255, col[2] + 20))
            dampen_col = (
                int(x)
                for x in colorsys.hsv_to_rgb(
                    dampen_col_hsv[0], dampen_col_hsv[1], dampen_col_hsv[2]
                )
            )
            image = await self.create_colored_image(
                self.no_data_img.width, self.no_data_img.height, dampen_col
            )

        aspect_ratio = image.width / image.height

        if width is None:
            width = int(height * aspect_ratio)

        if height is None:
            height = int(width / aspect_ratio)

        if x_offset is None:
            x_offset = -width * 0.5

        if y_offset is None:
            y_offset = -height * 0.5

        x_pos = int(anchor_data[anchor]['x'] + x_offset)
        y_pos = int(anchor_data[anchor]['y'] + y_offset)
        image = image.resize((width, height), Image.Resampling.LANCZOS)

        image = await self.apply_rounded_corners(image, width, height, 8)
        image.apply_transparency()

        drawImage.paste(image, (x_pos, y_pos), image)

    async def render_vertical_divider(
        self,
        drawLayer: ImageDraw.ImageDraw,
        anchor_data: dict,
        line_data: dict,
        color: str = '#ffffff',
    ) -> None:
        x_offset = line_data['x_offset']
        y_offset = line_data['y_offset']
        len = line_data['len']
        width = line_data['width']
        anchor = line_data['anchor']

        x_pos = anchor_data[anchor]['x'] + x_offset
        y_pos = anchor_data[anchor]['y'] + y_offset

        drawLayer.line(
            [(x_pos, y_pos), (x_pos, y_pos + len)],
            fill=color,
            width=width,
        )

    async def rgb_to_hex(self, rgb_tuple):
        """Convert RGB tuple to hex color"""

        if isinstance(rgb_tuple, str):
            return rgb_tuple
        r, g, b = rgb_tuple[:3]
        return f'#{r:02x}{g:02x}{b:02x}'

    async def hex_to_rgb(self, hex_code: str) -> tuple:
        """Converts HEX Code to RGB value"""

        hex_code = hex_code.lstrip('#')
        return tuple(int(hex_code[i : i + 2], 16) for i in (0, 2, 4))

    async def load_elements(self, user_data: UserData) -> dict:
        """Insert data into the json for elements"""

        raw_data = self.element_template.substitute(
            anime_count=user_data.anime_count,
            anime_eps=user_data.anime_eps,
            anime_mean=user_data.anime_mean_score,
            manga_count=user_data.manga_count,
            manga_chaps=user_data.manga_chaps,
            manga_mean=user_data.manga_mean_score,
        )

        data = json.loads(raw_data)
        return data

    async def load_anchors(self) -> dict:
        """Insert data into the json for anchors"""

        raw_data = self.anchor_template.substitute(
            width=IMG_WIDTH,
            height=IMG_HEIGHT,
            halfwidth=IMG_WIDTH * 0.5,
            halfheight=IMG_HEIGHT * 0.5,
        )

        data = json.loads(raw_data)
        return data

    async def generate(self, token: str, design: str = 'New') -> GenerationResponse:
        user_data = await fetch_user_data(token)

        if user_data.error:
            return GenerationResponse(False, user_data.error_msg)

        element_data = await self.load_elements(user_data)
        anchor_data = await self.load_anchors()

        self.primary_color_raw = (11, 22, 34)
        self.box_color_raw = ()
        self.text_color_from_image = await self.hex_to_rgb(user_data.profile_color)
        self.label_color_from_image = self.text_color_from_image

        if design.lower() == 'new' and user_data.banner_url != '':
            """ If banner is there and colored wrap is requested """

            image_response = requests.get(user_data.banner_url)
            banner = Image.open(BytesIO(image_response.content))
            (
                self.primary_color_raw,
                self.box_color_raw,
                self.text_color_from_image,
                self.label_color_from_image,
            ) = await colors.get_image_colors(banner)

        elif design.lower() == 'new' and user_data.profile_pic_url != '':
            """ If banner is not there and colored wrap is requested """

            image_response = requests.get(user_data.profile_pic_url)
            banner = Image.open(BytesIO(image_response.content))
            (
                self.primary_color_raw,
                self.box_color_raw,
                self.text_color_from_image,
                self.label_color_from_image,
            ) = await colors.get_image_colors(banner)

        # hex values from tuple values
        self.label_color_hex = await self.rgb_to_hex(self.label_color_from_image)
        self.text_color_hex = await self.rgb_to_hex(self.text_color_from_image)

        # darker the primary color to mimic the main wrawp without the alpha layering process
        alpha = 200 / 255
        darker_primary_color = (
            self.primary_color_raw[0] * alpha,
            self.primary_color_raw[1] * alpha,
            self.primary_color_raw[2] * alpha,
        )
        self.primary_color = tuple((int(x) for x in darker_primary_color))
        self.primary_color_hex = await self.rgb_to_hex(self.primary_color)

        r, g, b = self.primary_color

        # calculate the UNOFFICIAL color which is based on primary color but less saturated and higher brightness
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

        s = min(max(s - 0.20, 0.0), 1.0)
        v = min(max(v + 0.10, 0.0), 1.0)

        self.box_color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))
        self.box_color_hex = await self.rgb_to_hex(self.box_color)

        # calculate the ANIME/MANGA color which is based on primary color but less saturated and higher brightness
        h_l, s_l, v_l = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)

        s_l = min(max(s_l - 0.40, 0.0), 1.0)
        v_l = min(max(v_l + 0.30, 0.0), 1.0)

        self.l_box_color = tuple(
            int(c * 255) for c in colorsys.hsv_to_rgb(h_l, s_l, v_l)
        )
        self.l_box_color_hex = await self.rgb_to_hex(self.l_box_color)

        # generate the background image and round the corners
        bg = await self.create_colored_image(IMG_WIDTH, IMG_HEIGHT, self.primary_color)
        bg = await self.apply_rounded_corners(bg, IMG_WIDTH, IMG_HEIGHT, 8)

        draw = ImageDraw.ImageDraw(bg)

        await self.render_text(
            draw,
            anchor_data,
            element_data,
            element_data['unofficial'],
            self.box_color_hex,
        )
        await self.render_text(
            draw,
            anchor_data,
            element_data,
            element_data['heading'],
            self.text_color_hex,
        )

        # Anime Details
        await self.render_text(
            draw, anchor_data, element_data, element_data['anime'], self.l_box_color_hex
        )
        await self.render_image(
            bg,
            user_data.anime_img_url,
            anchor_data,
            element_data,
            element_data['anime_img'],
        )

        await self.render_text(
            draw,
            anchor_data,
            element_data,
            element_data['anime_count_text'],
            self.label_color_hex,
        )
        await self.render_text(
            draw,
            anchor_data,
            element_data,
            element_data['anime_eps_text'],
            self.label_color_hex,
        )
        await self.render_text(
            draw,
            anchor_data,
            element_data,
            element_data['anime_mean_text'],
            self.label_color_hex,
        )

        await self.render_text(
            draw, anchor_data, element_data, element_data['anime_count']
        )
        await self.render_text(
            draw, anchor_data, element_data, element_data['anime_eps']
        )
        await self.render_text(
            draw, anchor_data, element_data, element_data['anime_mean']
        )

        # Manga Details
        await self.render_text_right(
            draw, anchor_data, element_data, element_data['manga'], self.l_box_color_hex
        )
        await self.render_image(
            bg,
            user_data.manga_img_url,
            anchor_data,
            element_data,
            element_data['manga_img'],
        )

        element_data['manga_count'] = await self.render_text_right(
            draw,
            anchor_data,
            element_data,
            element_data['manga_count'],
        )
        element_data['manga_chaps'] = await self.render_text_right(
            draw,
            anchor_data,
            element_data,
            element_data['manga_chaps'],
        )
        element_data['manga_mean'] = await self.render_text_right(
            draw,
            anchor_data,
            element_data,
            element_data['manga_mean'],
        )

        await self.render_text_right(
            draw,
            anchor_data,
            element_data,
            element_data['manga_count_text'],
            self.label_color_hex,
        )
        await self.render_text_right(
            draw,
            anchor_data,
            element_data,
            element_data['manga_chaps_text'],
            self.label_color_hex,
        )
        await self.render_text_right(
            draw,
            anchor_data,
            element_data,
            element_data['manga_mean_text'],
            self.label_color_hex,
        )

        await self.render_text(
            draw, anchor_data, element_data, element_data['anime_highest_rated_text']
        )
        await self.render_text(
            draw, anchor_data, element_data, element_data['manga_highest_rated_text']
        )

        await self.render_vertical_divider(
            draw, anchor_data, element_data['divider'], self.box_color_hex
        )

        await self.render_text(
            draw,
            anchor_data,
            element_data,
            element_data['website'],
            self.l_box_color_hex,
        )

        img = await self.apply_rounded_corners(bg, bg.width, bg.height, 8)

        response = GenerationResponse()

        # grab binary image data from PIL image
        with BytesIO() as image_binary_container:
            img.save(image_binary_container, 'PNG')
            image_binary_container.seek(0)
            response.image_bytes = image_binary_container.read()
            response.username = user_data.name

        return response
