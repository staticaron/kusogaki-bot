import json
import pdb
from io import BytesIO
from string import Template

import requests
from PIL import Image, ImageDraw, ImageFont

from kusogaki_bot.features.aniwrap.fetch_data import UserData, fetch_user_data

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

ELEMENTS_FILE_LOCATION = 'kusogaki_bot/features/aniwrap/data/elements.json'
ANCHORS_FILE_LOCATION = 'kusogaki_bot/features/aniwrap/data/anchors.json'


class AniWrapService:
    def get_font(self, type: str, font_size: int):
        return ImageFont.truetype(FONT_LOCATION[type], font_size)

    def center_anchor_point(self, available_space: int, element_width: int) -> int:
        return int(available_space * 0.5 - element_width * 0.5)

    def render_text(
        self,
        drawLayer: ImageDraw.ImageDraw,
        anchor_data: dict,
        element_data: dict,
        text_data: dict,
    ) -> dict:
        """Fetch the data from the data container"""
        font_size = text_data['size']
        font_color = COLORS[text_data['color']]
        font_name = text_data['font']
        text = text_data['text']
        x_offset = text_data['x_offset']
        y_offset = text_data['y_offset']
        anchor = text_data.get('anchor', 'main_anchor')
        after = text_data.get('after', '')

        """Calculate the text Width and Height and save it in the data container"""
        font = self.get_font(font_name, font_size)
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
                element_data[after]['x_pos']
                + element_data[after]['width']
                + anchor_data[anchor]['vertical_spacing']
            )
            text_data['y_pos'] = element_data[after]['y_pos']

        drawLayer.text(
            (text_data['x_pos'], text_data['y_pos']),
            text,
            fill=font_color,
            font=font,
            features=['-kern'],
        )

        return text_data

    def render_text_right(
        self,
        drawLayer: ImageDraw.ImageDraw,
        anchor_data: dict,
        element_data: dict,
        text_data: dict,
    ) -> dict:
        """Fetch the data from the data container"""
        font_size = text_data['size']
        font_color = COLORS[text_data['color']]
        font_name = text_data['font']
        text = text_data['text']
        x_offset = text_data['x_offset']
        y_offset = text_data['y_offset']
        anchor = text_data.get('anchor', 'main_anchor')
        after = text_data.get('after', '')

        """Calculate the text Width and Height and save it in the data container"""
        font = self.get_font(font_name, font_size)
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
            fill=font_color,
            font=font,
            features=['-kern'],
        )

        return text_data

    def apply_rounded_corners(
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

    def render_image(
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

        image_response = requests.get(url)
        image: Image.Image = Image.open(BytesIO(image_response.content))

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

        image = self.apply_rounded_corners(image, width, height, 8)
        image.apply_transparency()

        drawImage.paste(image, (x_pos, y_pos), image)

    def render_vertical_divider(
        self, drawLayer: ImageDraw.ImageDraw, anchor_data: dict, line_data: dict
    ) -> None:
        x_offset = line_data['x_offset']
        y_offset = line_data['y_offset']
        len = line_data['len']
        width = line_data['width']
        color = line_data['color']
        anchor = line_data['anchor']

        x_pos = anchor_data[anchor]['x'] + x_offset
        y_pos = anchor_data[anchor]['y'] + y_offset

        drawLayer.line(
            [(x_pos, y_pos), (x_pos, y_pos + len)],
            fill=COLORS[color],
            width=width,
        )

    def load_elements(self, user_data: UserData) -> dict:
        """Insert data into the json for elements"""
        data = {}

        with open(ELEMENTS_FILE_LOCATION, 'r') as file_in:
            raw_data = file_in.read()
            template = Template(raw_data)
            raw_data = template.substitute(
                anime_count=user_data.anime_count,
                anime_eps=user_data.anime_eps,
                anime_mean=str(round(user_data.anime_mean_score, 1)) + '%',
                manga_count=user_data.manga_count,
                manga_chaps=user_data.manga_chaps,
                manga_mean=str(round(user_data.manga_mean_score, 1)) + '%',
            )

            data = json.loads(raw_data)

        return data

    def load_anchor(self) -> dict:
        """Insert data into the json for anchors"""
        data = {}

        with open(ANCHORS_FILE_LOCATION, 'r') as file_in:
            raw_data = file_in.read()
            template = Template(raw_data)
            raw_data = template.substitute(
                width=IMG_WIDTH,
                height=IMG_HEIGHT,
                halfwidth=IMG_WIDTH * 0.5,
                halfheight=IMG_HEIGHT * 0.5,
            )

            data = json.loads(raw_data)

        return data

    def generate(self, username: str) -> None:
        print('Hello from miniwrapgen!')

        user_data = fetch_user_data(username)

        if user_data.error:
            print(f'ERROR : \n{user_data.error_msg}')
            return None

        element_data = self.load_elements(user_data)
        anchor_data = self.load_anchor()

        img = Image.new('RGBA', (IMG_WIDTH, IMG_HEIGHT), color=COLORS['bg'])

        draw = ImageDraw.Draw(img)

        self.render_text(draw, anchor_data, element_data, element_data['unofficial'])
        self.render_text(draw, anchor_data, element_data, element_data['heading'])

        # Anime Details
        self.render_text(draw, anchor_data, element_data, element_data['anime'])
        self.render_image(
            img,
            user_data.anime_img_url,
            anchor_data,
            element_data,
            element_data['anime_img'],
        )

        self.render_text(
            draw, anchor_data, element_data, element_data['anime_count_text']
        )
        self.render_text(
            draw, anchor_data, element_data, element_data['anime_eps_text']
        )
        self.render_text(
            draw, anchor_data, element_data, element_data['anime_mean_text']
        )

        self.render_text(draw, anchor_data, element_data, element_data['anime_count'])
        self.render_text(draw, anchor_data, element_data, element_data['anime_eps'])
        self.render_text(draw, anchor_data, element_data, element_data['anime_mean'])

        # Manga Details
        self.render_text(draw, anchor_data, element_data, element_data['manga'])
        self.render_image(
            img,
            user_data.manga_img_url,
            anchor_data,
            element_data,
            element_data['manga_img'],
        )

        element_data['manga_count'] = self.render_text_right(
            draw, anchor_data, element_data, element_data['manga_count']
        )
        element_data['manga_chaps'] = self.render_text_right(
            draw, anchor_data, element_data, element_data['manga_chaps']
        )
        element_data['manga_mean'] = self.render_text_right(
            draw, anchor_data, element_data, element_data['manga_mean']
        )

        self.render_text_right(
            draw, anchor_data, element_data, element_data['manga_count_text']
        )
        self.render_text_right(
            draw, anchor_data, element_data, element_data['manga_chaps_text']
        )
        self.render_text_right(
            draw, anchor_data, element_data, element_data['manga_mean_text']
        )

        self.render_text(
            draw, anchor_data, element_data, element_data['anime_highest_rated_text']
        )
        self.render_text(
            draw, anchor_data, element_data, element_data['manga_highest_rated_text']
        )

        self.render_vertical_divider(draw, anchor_data, element_data['divider'])

        img = self.apply_rounded_corners(img, IMG_WIDTH, IMG_HEIGHT, 8)

        img.save(f'wraps/{username}.png')
