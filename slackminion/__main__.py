import logging
import sys
sys.path.append('.')

from config import *
from slackminion.bot import Bot


def main():
    level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    bot = Bot(SLACK_TOKEN)
    bot.start()
    bot.run()
    bot.stop()

if __name__ == "__main__":
    main()
