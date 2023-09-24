import sys
import logging
from algosdk.v2client.algod import AlgodClient
from nfdlookup.client import NFDMainnetClient
from algosdk.encoding import is_valid_address


logging.basicConfig(level=logging.DEBUG)


def print_addresses(client: NFDMainnetClient, name: str):
    filter_out = ["i.commission", "i.seller"]
    res = client.lookup_name(name)
    if res is not None:
        for key in res:
            if key.endswith(".a"):
                if not any(key.startswith(prefix) for prefix in filter_out):
                    print(f"{key}: {res[key]}")
            elif key.endswith(".as"):
                for n, val in enumerate(res[key]):
                    print(f"{key}[{n}]: {val}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} nfd[.algo] | ADDRESS")
        sys.exit(0)

    algod_address = "https://mainnet-api.algonode.cloud"
    algod_token = ""
    algod = AlgodClient(algod_token, algod_address)
    client = NFDMainnetClient(algod)

    for arg in sys.argv[1:]:
        if is_valid_address(arg):
            names = client.lookup_address(arg)
            for name in names:
                print(name)
        elif arg.endswith(".algo"):
            print_addresses(client, arg)
        else:
            print_addresses(client, arg + ".algo")


if __name__ == "__main__":
    main()
