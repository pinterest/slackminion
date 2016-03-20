import argparse
import logging
import yaml

from slackminion.bot import Bot


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', action='store', default='config.yaml', help='Specify a config file (default: config.yaml)')
    p.add_argument('--test', action='store_true', help='Load plugins and exit')
    args = p.parse_args()

    with open(args.config, 'rb') as f:
        config = yaml.load(f)

    level = logging.DEBUG if config['debug'] else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    bot = Bot(config)
    bot.start()
    if not args.test:
        bot.run()
    bot.stop()

if __name__ == "__main__":
    main()
