import string


def is_template_str(s: str) -> bool:
    """
    Check if a string is a template string.
    See: https://stackoverflow.com/a/46161774/2369823

    Args:
        s: A string to check.
    """
    for item in string.Formatter().parse(s):
        if item[1] is not None:
            return True

    return False
