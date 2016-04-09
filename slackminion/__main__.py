import argparse
import logging
import signal
import sys
import yaml

from slackminion.bot import Bot


def main():
    def sigterm_handler(signum, frame):
        bot.runnable = False

    p = argparse.ArgumentParser()
    p.add_argument('--config', action='store', default='config.yaml', help='Specify a config file (default: config.yaml)')
    p.add_argument('--test', action='store_true', help='Load plugins and exit')
    args = p.parse_args()

    with open(args.config, 'rb') as f:
        config = yaml.load(f)

    level = logging.DEBUG if config['debug'] else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(name)s %(levelname)s: %(message)s')

    bot = Bot(config, args.test)
    bot.start()
    if not args.test:
        signal.signal(signal.SIGTERM, sigterm_handler)
        bot.run()
    bot.stop()

    if args.test:
        test_passed = True
        output = ["Bot Test Results"]
        metrics = bot.plugins.metrics
        output.append("Plugins Loaded")
        for p in bot.plugins.plugins:
            context = {
                'name': type(p).__name__,
                'version': '-'.join([p._version, p._commit]),
                'load_time': metrics['load_times'][type(p).__name__]
            }
            output.append("{name:<30} {version:<20} {load_time:>7.03f} ms".format(**context))
        if len(metrics['plugins_failed']) > 0:
            output.append("")
            output.append("Plugins failed to load")
            for p in metrics['plugins_failed']:
                output.append(p)
        output.append("")
        output.append("Bot startup time: %.03f ms" % bot.metrics['startup_time'])
        output.append("Plugins: %d total, %d loaded, %d failed" % (metrics['plugins_total'], metrics['plugins_loaded'], len(metrics['plugins_failed'])))
        if metrics['plugins_total'] != metrics['plugins_loaded']:
            output.append("")
            output.append("=== Bot Failed Startup Tests ===")
            test_passed = False
        logging.getLogger().info('\n'.join(output))

        if not test_passed:
            sys.exit(1)

if __name__ == "__main__":
    main()
