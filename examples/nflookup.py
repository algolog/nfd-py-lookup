import sys
import logging
import argparse
from algosdk.v2client.algod import AlgodClient
from nfdlookup.client import NFDMainnetClient
from algosdk.encoding import is_valid_address


def print_addresses(client: NFDMainnetClient, name: str, show_all=True):
    res = client.lookup_name(name)
    if res is not None:
        for key in res:
            if key.endswith(".a"):
                # show only owner address unless asked for more
                if show_all or key.startswith("i.owner"):
                    print(f"{key}: {res[key]}")
            elif key.endswith(".as"):
                for n, val in enumerate(res[key]):
                    print(f"{key}[{n}]: {val}")


def main():
    parser = argparse.ArgumentParser(description="NFD lookup")
    parser.add_argument("query", metavar="nfd[.algo] | ADDRESS", help="NFD name or address")
    parser.add_argument("--algod-address", default="https://mainnet-api.algonode.cloud", help="URL of Algod node to connect to")
    parser.add_argument("--algod-token", default="", help="API key for algod node (if needed)")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug info")
    parser.add_argument("-a", "--all", action="store_true",
                        help="include opted & owned NFDs in address lookups; show all addresses in name lookups")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    algod = AlgodClient(args.algod_token, args.algod_address)
    client = NFDMainnetClient(algod)
    query = args.query

    if is_valid_address(query):
        names = client.lookup_address(query)
        if args.all:
            names = set(names)
            names.update(
                client.lookup_opted_and_owned_by(query)
            )
        for name in sorted(names):
            print(name)
    elif query.endswith(".algo"):
        print_addresses(client, query, show_all=args.all)
    else:
        print_addresses(client, query + ".algo", show_all=args.all)


if __name__ == "__main__":
    main()
