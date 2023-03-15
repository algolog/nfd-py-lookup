from base64 import b64encode, b64decode
from algosdk.encoding import encode_address
from algosdk.constants import ZERO_ADDRESS


def encode_uvarint(x):
    buf = b""
    while x >= 0x80:
        buf += bytes([(x & 0xFF) | 0x80])
        x >>= 7
    buf += bytes([x & 0xFF])
    return buf


def unpack_uints(data: bytes):
    """
    Returns all non-zero 64-bit ints contained in the slice (up to 15 for a single
    local-state fetch)
    """
    if len(data) % 8 != 0:
        raise ValueError('data length {} is not a multiple of 8'.format(len(data)))
    result = []
    offset = 0
    while offset < len(data):
        ival = int.from_bytes(data[offset:offset+8], "big")
        offset += 8
        if ival != 0:
            result.append(ival)
    return result


def unpack_addresses(data: bytes) -> list:
    """Returns all non-zero Algorand 32-byte PKs encoded in a value (up to 3)"""
    if len(data) % 32 != 0:
        raise ValueError('data length {} is not a multiple of 32'.format(len(data)))
    algo_addresses = []
    offset = 0
    while offset < len(data):
        addr = encode_address(data[offset:offset+32])
        offset += 32
        if addr != ZERO_ADDRESS:
            algo_addresses.append(addr)
    return algo_addresses


def get_app_info_bytes(app_info, key):
    """Get bytes value from application info local state dict for given key."""
    if type(key) == str:
        key = b64encode(key.encode())

    key_vals = app_info['app-local-state']['key-value']
    value = {'bytes': ''}
    for kv in key_vals:
        if kv['key'] == key.decode():
            value = kv['value']
    return b64decode(value['bytes'])


def format_state_keys(state):
    """Format state dict by base64 decoding keys"""
    formatted_state = {}
    for item in state:
        key = item["key"]
        value = item["value"]
        try:
            formatted_key = b64decode(key).decode("utf-8")
        except:
            formatted_key = b64decode(key)
        if value["type"] == 1:
            formatted_state[formatted_key] = value["bytes"]  # byte string
        else:
            formatted_state[formatted_key] = value["uint"]   # integer
    return formatted_state


def get_global_state(algod_client, app_id):
    """Returns dict of global state for application with the given app_id"""
    try:
        app_info = algod_client.application_info(app_id)
    except:
        raise Exception("Application does not exist.")
    return format_state_keys(app_info["params"]["global-state"])
