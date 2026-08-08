def register(subparsers):

    parser = subparsers.add_parser("activate")

    parser.add_argument("name")

    parser.set_defaults(func=activate_run)


def activate_run():
    return
