from algosdk.transaction import LogicSigAccount
from .constants import LOOKUP_LOGIC_SIG_TEMPLATE
from .utils import encode_uvarint


def get_lookup_logicsig(prefix: str, lookup_str: str, registry_app_id: int) -> LogicSigAccount:
    program = bytearray(LOOKUP_LOGIC_SIG_TEMPLATE)
    program[6:14] = registry_app_id.to_bytes(8, 'big')
    bytes_to_append = (prefix + lookup_str).encode()
    program += encode_uvarint(len(bytes_to_append))
    program += bytes_to_append
    return LogicSigAccount(program)


def get_nfd_revaddress_logicsig(address: str, registry_app_id: int):
    lsig = get_lookup_logicsig('address/', address, registry_app_id)
    return lsig


def get_nfd_name_logicsig(nfd_name: str, registry_app_id: int):
    lsig = get_lookup_logicsig('name/', nfd_name, registry_app_id)
    return lsig
