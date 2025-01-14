import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlparse


class ImageFormat(Enum):
    """Supported image formats"""

    PNG = '.png'
    JPG = '.jpg'
    JPEG = '.jpeg'
    GIF = '.gif'
    WEBP = '.webp'


@dataclass
class ImageSource:
    """
    Represents a processed image source with detailed information.

    Attributes:
        url (str): The processed and normalized image URL
        source_type (str): The type of image source ('imgur', 'kusogaki', 'other')
        image_format (Optional[ImageFormat]): The detected image format
        original_url (Optional[str]): The original, unprocessed URL
    """

    url: str
    source_type: str
    image_format: Optional[ImageFormat] = None
    original_url: Optional[str] = None


class ImageUrlHandler:
    """
    Handles transformation and validation of image URLs from various sources.

    This class provides methods to process, transform, and validate image URLs,
    with special handling for Imgur and Kusogaki URLs.
    """

    IMGUR_PATTERN = re.compile(r'https?://(?:i\.)?imgur\.com/(\w+)(?:\.\w+)?')
    KUSOGAKI_PATTERN = re.compile(
        r'https://kusogaki\.co/images/([^/]+/[^/]+/[^/]+)(?:\.\w+)?'
    )

    SUPPORTED_FORMATS = {fmt.value for fmt in ImageFormat}

    @classmethod
    def transform_url(cls, url: str) -> str:
        """
        Transform various image URLs into their direct form.

        Args:
            url (str): The original URL to transform

        Returns:
            str: The transformed URL that directly points to the image

        Example:
            >>> ImageUrlHandler.transform_url('https://imgur.com/abcd123')
            'https://i.imgur.com/abcd123.png'
        """
        if not url:
            return url

        imgur_match = cls.IMGUR_PATTERN.match(url)
        if imgur_match:
            return f'https://i.imgur.com/{imgur_match.group(1)}.png'

        kusogaki_match = cls.KUSOGAKI_PATTERN.match(url)
        if kusogaki_match:
            base_path = kusogaki_match.group(1)
            if not cls._has_image_extension(url):
                return f'https://kusogaki.co/images/{base_path}.png'
            return url

        if not cls._has_image_extension(url):
            url = f"{url.rstrip('/')}.png"

        return url

    @classmethod
    def process_url(cls, url: str) -> ImageSource:
        """
        Process URL and return detailed information about the image source.

        Args:
            url (str): The URL to process

        Returns:
            ImageSource: A dataclass containing processed URL information including
                        the normalized URL, source type, image format, and original URL

        Example:
            >>> source = ImageUrlHandler.process_url('https://imgur.com/abcd123')
            >>> print(source.source_type)
            'imgur'
        """
        original_url = url
        url = cls.transform_url(url)

        if cls.IMGUR_PATTERN.match(url):
            source_type = 'imgur'
        elif cls.KUSOGAKI_PATTERN.match(url):
            source_type = 'kusogaki'
        else:
            source_type = 'other'

        image_format = cls._get_image_format(url)

        return ImageSource(
            url=url,
            source_type=source_type,
            image_format=image_format,
            original_url=original_url,
        )

    @classmethod
    def is_kusogaki_url(cls, url: str) -> bool:
        """
        Check if URL is from kusogaki.co.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if the URL is from kusogaki.co, False otherwise

        Example:
            >>> ImageUrlHandler.is_kusogaki_url('https://kusogaki.co/images/abc/def/ghi.png')
            True
        """
        return bool(cls.KUSOGAKI_PATTERN.match(url))

    @classmethod
    def is_imgur_url(cls, url: str) -> bool:
        """
        Check if URL is from imgur.com.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if the URL is from imgur.com, False otherwise

        Example:
            >>> ImageUrlHandler.is_imgur_url('https://imgur.com/abcd123')
            True
        """
        return bool(cls.IMGUR_PATTERN.match(url))

    @classmethod
    def get_cache_key(cls, url: str) -> str:
        """
        Get a unique key for image caching based on URL.

        Args:
            url (str): The URL to generate a cache key for

        Returns:
            str: A cache key string combining netloc and path, excluding query parameters

        Example:
            >>> ImageUrlHandler.get_cache_key('https://example.com/img/photo.png?size=large')
            'example.com/img/photo.png'
        """
        parsed = urlparse(url)
        clean_path = parsed.path.split('?')[0].split('#')[0]
        return f'{parsed.netloc}{clean_path}'

    @classmethod
    def _has_image_extension(cls, url: str) -> bool:
        """
        Check if URL ends with a supported image extension.

        Args:
            url (str): The URL to check

        Returns:
            bool: True if the URL ends with a supported image extension, False otherwise
        """
        return any(url.lower().endswith(ext) for ext in cls.SUPPORTED_FORMATS)

    @classmethod
    def _get_image_format(cls, url: str) -> Optional[ImageFormat]:
        """
        Get the image format from the URL.

        Args:
            url (str): The URL to extract the image format from

        Returns:
            Optional[ImageFormat]: The detected ImageFormat enum value, or None if no valid format is found
        """
        ext = '.' + url.split('.')[-1].lower() if '.' in url else None
        try:
            return next(fmt for fmt in ImageFormat if fmt.value == ext)
        except StopIteration:
            return None
