def register(subparsers):

    parser = subparsers.add_parser("delete")

    parser.add_argument("name")

    parser.set_defaults(func=delete_run)


def delete_run():
    return
