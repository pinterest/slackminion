import logging

from config import *
from slackminion.bot import Bot


if __name__ == "__main__":
    level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    bot = Bot(SLACK_TOKEN)
    bot.start()
    bot.run()
    bot.stop()
