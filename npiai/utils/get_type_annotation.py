from typing import get_args


def get_type_annotation(t: type) -> type:
    args = get_args(t)

    if len(args) == 2 and args[1] is type(None):
        return args[0]

    return t
