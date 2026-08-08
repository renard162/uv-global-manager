def register(subparsers):

    parser = subparsers.add_parser("list")

    parser.add_argument("name")

    parser.set_defaults(func=list_run)


def list_run():
    return
