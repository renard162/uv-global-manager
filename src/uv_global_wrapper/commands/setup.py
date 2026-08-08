def register(subparsers):

    parser = subparsers.add_parser("setup")

    parser.add_argument("name")

    parser.set_defaults(func=setup_run)


def setup_run():
    return
