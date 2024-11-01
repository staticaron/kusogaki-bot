import logging
from functools import lru_cache
from typing import Optional

import redis


class Database:
    """Singleton class to manage Redis database connection."""

    _instance: Optional[redis.Redis] = None

    @classmethod
    @lru_cache(maxsize=1)
    def get_instance(cls) -> redis.Redis:
        """
        Get Redis connection instance using singleton pattern.
        Uses lru_cache to ensure only one instance is created.
        """
        if cls._instance is None:
            from config import DB_HOST, DB_PASSWORD, DB_PORT

            try:
                cls._instance = redis.Redis(
                    host=DB_HOST,
                    port=int(DB_PORT) if DB_PORT else 6379,
                    password=DB_PASSWORD,
                    ssl=True,
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                cls._instance.ping()
                logging.info('Successfully connected to Redis database')
            except redis.RedisError as e:
                logging.error(f'Failed to connect to Redis: {str(e)}')
                raise

        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close the Redis connection if it exists."""
        if cls._instance is not None:
            try:
                cls._instance.close()
                cls._instance = None
                cls.get_instance.cache_clear()
                logging.info('Redis connection closed')
            except redis.RedisError as e:
                logging.error(f'Error closing Redis connection: {str(e)}')
