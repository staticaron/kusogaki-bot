import sys

import config
from kusogaki_bot.core.bot import KusogakiBot
from kusogaki_bot.shared.services import logger


def main():
    """
    Initialize and run the Discord bot
    """

    is_test = sys.argv[1].lower() == 'test' if len(sys.argv) > 1 else False

    try:
        bot = KusogakiBot(is_test)

        if is_test and config.TEST_TOKEN is not None:
            bot.run(config.TEST_TOKEN)
        elif config.TOKEN is not None:
            bot.run(config.TOKEN)
    except Exception as e:
        logger.logger.error(f'Failed to start bot: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
