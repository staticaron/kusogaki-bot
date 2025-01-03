from config import TOKEN
from kusogaki_bot.bot import Kusogaki


def main():
    bot = Kusogaki()
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
