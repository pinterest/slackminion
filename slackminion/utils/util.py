import textwrap


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
