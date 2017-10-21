import argparse
import json
import sys

from .indexer import Indexer

indexer = Indexer()


def describe(args):
    indexer.index_file(args.filename)
    return indexer.lookup_metadata(args.filename, args.line, args.column)


def find_definition(args):
    indexer.index_file(args.filename)
    return indexer.lookup_definition(args.filename, args.line, args.column)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    describe_parser = subparsers.add_parser("describe", help="Describe the thing at point.")
    describe_parser.set_defaults(func=describe)

    find_definition_parser = subparsers.add_parser("find_definition", help="Find where the thing at point is defined.")
    find_definition_parser.set_defaults(func=find_definition)

    for p in (describe_parser, find_definition_parser):
        p.add_argument("filename", help="The name of the file to analyze.")
        p.add_argument("line", type=int)
        p.add_argument("column", type=int)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_usage()
        return 1

    res = args.func(args)
    sys.stdout.write(json.dumps(res, indent=4))
    return 0


if __name__ == "__main__":
    sys.exit(main())
