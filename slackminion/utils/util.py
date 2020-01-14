from slackminion.slack import SlackUser, SlackConversation
import textwrap
import asyncio
import os
import getpass


def format_docstring(docstring):
    """
    Uses textwrap to auto-dedent a docstring (removes leading spaces)
    Returns the docstring in a pre-formatted block with required characters escaped.
    https://api.slack.com/docs/message-formatting
    :param docstring: str
    :return: str
    """
    if not docstring:
        return ''
    formatted_text = '```{}```'.format(
        textwrap.dedent(docstring.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
                        )
    )
    return formatted_text


def output_to_dev_console(text):
    try:
        console_width = min(int(os.popen('stty size', 'r').read().split()[1]), 120) - 20
    except Exception:
        console_width = 80
    banner_text = ' COMMAND OUTPUT '
    padding = '=' * ((console_width - len(banner_text)) // 2)
    banner = padding + banner_text + padding
    print(banner + os.linesep + text + os.linesep + '=' * len(banner))


async def dev_console(bot):
    import readline  # noqa -- only the import is needed for readline support in input
    banner = 'Slackminion: Starting DEV MODE'
    if hasattr(bot, 'user_manager'):
        delattr(bot, 'user_manager')
    await asyncio.sleep(1)
    print(banner)
    print('=' * len(banner))
    print("""
    Note: Plugins loaded in this mode will send all output to
    the test window, rather than to slack.

    However, the commands themselves are not modified in any way.
    Typing commands from any loaded plugins ** WILL ACTUALLY RUN THE COMMAND **
    and any backend code associated. Only OUTPUT is suppressed.
    """)
    while not bot.webserver.thread.is_alive:
        print('Waiting for webserver to start...')
        await asyncio.sleep(1)
    while bot.runnable:
        try:
            command = input("Slackminion DEV_MODE (type a !command.  use 'exit' to leave)> ")
            if command.lower() in ['quit', 'exit']:
                bot.runnable = False
                continue
            elif len(command) == 0:
                continue
        except (KeyboardInterrupt, EOFError) as e:
            bot.log.exception('Caught {}'.format(e))
            bot.runnable = False
            raise
        user = SlackUser(user_id="UDEVMODE")
        channel_id = 'CDEVMODE'
        channel = SlackConversation(None, None)
        channel.load(channel_id)
        user._username = getpass.getuser()
        payload = {
            'data': {
                'user': user,
                'channel': channel,
                'text': command,
                'ts': None,
            }
        }
        await bot._event_message(**payload)
