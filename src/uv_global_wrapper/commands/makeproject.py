def register(subparsers):

    parser = subparsers.add_parser("make-project")

    parser.add_argument("name")

    parser.set_defaults(func=make_run)


def make_run():
    return
