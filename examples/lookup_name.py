import sys
from nfdlookup.client import NFDMainnetClient
from pprint import pprint

name = sys.argv[1] if len(sys.argv) > 1 else 'nfdomains.algo'
print(f"Forward lookup for name: {name}")

client = NFDMainnetClient()
addresses = client.lookup_name(name)
pprint(addresses)
