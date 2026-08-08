def register(subparsers):

    parser = subparsers.add_parser("create", help="Create a new environment.")

    parser.add_argument("name")

    parser.add_argument("--python", default="3.13")

    parser.set_defaults(func=create_run)


def create_run(args):

    print(args.name)
    print(args.python)
