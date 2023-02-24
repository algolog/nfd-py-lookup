from base64 import b64encode, b64decode
from algosdk.encoding import encode_address
from .utils import unpack_addresses


class NFDProperties:
    def __init__(self, key_formatted_state: dict):
        self.state = key_formatted_state

    def fetch_name(self):
        return b64decode(self.state['i.name']).decode()

    def fetch_addresses(self):
        """Extract address-related NFD properties from key-formatted state"""
        properties = {}
        for key, value in self.state.items():
            if key.endswith('.a'):
                properties[key] = encode_address(b64decode(value))
            elif key.endswith('.as'):
                # caAlgo.#.as (sets of packed algorand addresses)
                properties[key] = unpack_addresses(b64decode(value))
        return properties
