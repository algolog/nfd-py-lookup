import sys
from algosdk.v2client.algod import AlgodClient
from nfdlookup.client import NFDMainnetClient
from algosdk.encoding import is_valid_address


def print_addresses(client: NFDMainnetClient, name: str):
    res = client.lookup_name(name)
    if res is not None:
        for key in res:
            if key == "i.owner.a":
                print(f"{key}: {res[key]}")
            elif key.endswith(".as"):
                for n, val in enumerate(res[key]):
                    print(f"{key}[{n}]: {val}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} nfd[.algo] | ADDRESS")
        sys.exit(0)

    algod_address = ""
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
