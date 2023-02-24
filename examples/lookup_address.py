import sys
from nfdlookup.client import NFDMainnetClient

NFD_ADDRESS = 'RSV2YCHXA7MWGFTX3WYI7TVGAS5W5XH5M7ZQVXPPRQ7DNTNW36OW2TRR6I'
addr = sys.argv[1] if len(sys.argv) > 1 else NFD_ADDRESS
print(f"Reverse lookup for address: {addr}")

client = NFDMainnetClient()
names = client.lookup_address(addr)
print(names)
