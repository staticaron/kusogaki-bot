import asyncio
import io
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import aiohttp
from discord import File

from kusogaki_bot.shared.utils.images import ImageSource, ImageUrlHandler

logger = logging.getLogger(__name__)


class ImageCache:
    """Enhanced image cache with TTL and size limits

    A cache implementation for storing image data with time-to-live (TTL) and maximum size constraints.
    Uses an async lock for thread-safe operations.

    Attributes:
        _cache (Dict[str, Tuple[bytes, datetime]]): Internal cache storage mapping keys to tuples of (data, timestamp)
        _max_size (int): Maximum number of items to store in cache
        _ttl (timedelta): Time-to-live duration for cached items
        _lock (asyncio.Lock): Async lock for thread-safe operations
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        """Initialize the image cache with size and TTL constraints.

        Args:
            max_size (int, optional): Maximum number of items to store. Defaults to 1000.
            ttl_seconds (int, optional): Time-to-live in seconds. Defaults to 3600.
        """
        self._cache: Dict[str, Tuple[bytes, datetime]] = {}
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[bytes]:
        """Retrieve an item from the cache if it exists and hasn't expired.

        Args:
            key (str): The cache key to retrieve

        Returns:
            Optional[bytes]: The cached image data if found and valid, None otherwise
        """
        async with self._lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if datetime.now() - timestamp < self._ttl:
                    return data
                del self._cache[key]
        return None

    async def set(self, key: str, data: bytes) -> None:
        """Store an item in the cache with the current timestamp.

        If cache is at capacity, removes the oldest half of the entries.

        Args:
            key (str): The cache key to store
            data (bytes): The image data to cache
        """
        async with self._lock:
            if len(self._cache) >= self._max_size:
                sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
                self._cache = dict(sorted_items[len(sorted_items) // 2 :])

            self._cache[key] = (data, datetime.now())


class ImageService:
    """Service for handling image operations with improved error handling

    Provides functionality for fetching, caching, and managing images from various sources
    with built-in error handling and retry mechanisms.

    Attributes:
        session (Optional[aiohttp.ClientSession]): HTTP client session for making requests
        cache (ImageCache): Instance of ImageCache for storing retrieved images
        _session_lock (asyncio.Lock): Lock for thread-safe session management
    """

    def __init__(self) -> None:
        """Initialize the image service with a cache and session lock."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = ImageCache(max_size=1000, ttl_seconds=3600)
        self._session_lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get or create an aiohttp ClientSession with configured timeout and connection pooling.

        This method ensures that only one active session exists at a time. It creates a new
        session if none exists or if the current one is closed. Session creation is
        thread-safe using an async lock.

        The session is configured with:
            - 10 second timeout
            - Connection pool limit of 100
            - 300 second DNS cache TTL
            - Connection reuse enabled

        Returns:
            aiohttp.ClientSession: An active session for making HTTP requests

        Note:
            The session is reused across requests to maximize connection reuse and
            minimize resource usage. The session is automatically recreated if closed.

        Raises:
            aiohttp.ClientError: If session creation fails due to network or configuration issues
            asyncio.TimeoutError: If session creation times out
        """
        async with self._session_lock:
            if self.session is None or self.session.closed:
                timeout = aiohttp.ClientTimeout(total=10)
                conn = aiohttp.TCPConnector(
                    limit=100, ttl_dns_cache=300, force_close=False
                )
                self.session = aiohttp.ClientSession(timeout=timeout, connector=conn)
            return self.session

    def _get_headers(self, image_source: ImageSource) -> dict:
        """Get appropriate headers based on image source.

        Configures request headers based on the source type of the image.

        Args:
            image_source (ImageSource): Source information for the image

        Returns:
            dict: Dictionary of HTTP headers appropriate for the image source
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        if image_source.source_type == 'imgur':
            headers.update(
                {
                    'Referer': 'https://imgur.com/',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                }
            )
        elif image_source.source_type == 'kusogaki':
            headers.update(
                {
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://kusogaki.co/',
                }
            )

        return headers

    async def fetch_image(self, url: str, retries: int = 3) -> Optional[bytes]:
        """Fetch image data from URL with retry mechanism.

        Attempts to fetch image data with configurable retry attempts and
        intelligent error handling for different HTTP status codes.

        Args:
            url (str): URL of the image to fetch
            retries (int, optional): Number of retry attempts. Defaults to 3.

        Returns:
            Optional[bytes]: The image data if successfully fetched, None otherwise
        """
        session = await self.get_session()
        image_source = ImageUrlHandler.process_url(url)
        headers = self._get_headers(image_source)

        for attempt in range(retries):
            try:
                async with session.get(image_source.url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    elif response.status == 404:
                        logger.error(f'Image not found: {image_source.url}')
                        return None
                    elif response.status == 403:
                        logger.error(f'Access forbidden: {image_source.url}')
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (compatible; Discord Bot)'
                        }
                    elif response.status >= 500:
                        if attempt < retries - 1:
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(
                    f'Attempt {attempt + 1} failed for {image_source.url}: {str(e)}'
                )
                if attempt < retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue

        logger.error(
            f'Failed to fetch image after {retries} attempts: {image_source.url}'
        )
        return None

    async def get_image_data(self, url: str) -> Optional[bytes]:
        """Retrieve image data with caching support.

        Attempts to get image data from cache first, falling back to
        fetching from source if not cached or expired.

        Args:
            url (str): URL of the image to retrieve

        Returns:
            Optional[bytes]: The image data if available, None if retrieval fails
        """
        cache_key = ImageUrlHandler.get_cache_key(url)

        data = await self.cache.get(cache_key)
        if data:
            return data

        data = await self.fetch_image(url)
        if data:
            await self.cache.set(cache_key, data)
        return data

    async def preload_images(self, urls: list[str]) -> None:
        """Preload multiple images with improved host grouping.

        Efficiently preloads multiple images by grouping requests by source
        and implementing appropriate rate limiting.

        Args:
            urls (list[str]): List of image URLs to preload
        """
        grouped_urls: Dict[str, list] = {'imgur': [], 'kusogaki': [], 'other': []}

        for url in urls:
            image_source = ImageUrlHandler.process_url(url)
            grouped_urls[image_source.source_type].append(url)

        tasks = []

        for url in grouped_urls['imgur']:
            if not await self.cache.get(ImageUrlHandler.get_cache_key(url)):
                tasks.append(self.get_image_data(url))
                await asyncio.sleep(0.1)

        for source_type in ['kusogaki', 'other']:
            source_tasks = [
                self.get_image_data(url)
                for url in grouped_urls[source_type]
                if not await self.cache.get(ImageUrlHandler.get_cache_key(url))
            ]
            tasks.extend(source_tasks)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_image_file(self, url: str) -> Optional[File]:
        """Convert image data to Discord File object.

        Handles both URL and local file paths, converting image data
        into a format suitable for Discord messages.

        Args:
            url (str): URL or file path of the image

        Returns:
            Optional[File]: Discord File object if successful, None otherwise
        """
        try:
            if not url.startswith(('http://', 'https://')):
                path = Path(url)
                return File(path) if path.exists() else None

            data = await self.get_image_data(url)
            if data:
                image_source = ImageUrlHandler.process_url(url)
                filename = image_source.url.split('/')[-1].split('?')[0]
                return File(io.BytesIO(data), filename=filename)

        except Exception as e:
            logger.error(f'Error getting image file for {url}: {str(e)}')
            return None

    async def cleanup(self):
        """Cleanup resources by closing the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


image_service = ImageService()
