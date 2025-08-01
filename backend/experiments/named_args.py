"""Experiment with processing of *args and **kwargs params."""
from datetime import datetime


def parse_args(*args, **kwargs):
    """Parse and display parameter values."""
    print("parse_args: args =", args, "kwargs =", kwargs)
    # Extract limit and offset
    limit = kwargs.get('limit', 0)
    offset = kwargs.get('offset', 0)
    if 'limit' in kwargs: del kwargs['limit']  # noqa: E701 multiple statements on line
    if 'offset' in kwargs: del kwargs['offset']  # noqa: E701 multiple statements on line
    print(f"limit={limit} is a {type(limit)}")
    print(f"offset={offset} is a {type(offset)}")
    for k, v in kwargs.items():
        print(k, "=", v)


def main():
    """Do it."""
    parse_args(user="jim", age=25, now=datetime.now())
    parse_args(user="jim", age=25, limit=5, now=datetime.now())
    parse_args(user="jim", age=25, limit=5, offset=4, now=datetime.now())


if __name__ == '__main__':
    main()
