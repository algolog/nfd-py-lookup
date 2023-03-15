from base64 import b64encode, b64decode
from algosdk.v2client.algod import AlgodClient
from algosdk.error import AlgodHTTPError
from algosdk.encoding import decode_address, encode_address
from .constants import TESTNET_REGISTRY_APP_ID, MAINNET_REGISTRY_APP_ID
from .contracts import get_nfd_name_logicsig, get_nfd_revaddress_logicsig
from .nfdproperties import NFDProperties
from .utils import unpack_uints, get_global_state, get_app_info_bytes


class NFDClient:
    def __init__(self, algod_client: AlgodClient, registry_app_id: int, network: str):
        self.algod = algod_client
        self.registry_app_id = registry_app_id
        self.network = network

    def find_nfd_app_id_by_name(self, nfd_name: str):
        lsig = get_nfd_name_logicsig(nfd_name, self.registry_app_id)
        address = lsig.address()
        try:
            info = self.algod.account_application_info(address, self.registry_app_id)
        except AlgodHTTPError:
            return None
        app_id = int.from_bytes(get_app_info_bytes(info, 'i.appid'), 'big')
        return app_id

    def find_nfd_app_ids_by_address(self, lookup_address: str) -> list[int]:
        b_address = decode_address(lookup_address)
        lsig = get_nfd_revaddress_logicsig(encode_address(b_address), self.registry_app_id)
        address = lsig.address()
        try:
            info = self.algod.account_application_info(address, self.registry_app_id)
        except AlgodHTTPError:
            return None
        app_ids = unpack_uints(get_app_info_bytes(info, 'i.apps0'))
        return app_ids

    def lookup_address(self, address: str) -> list[str]:
        """Return list of names associated with address (reverse lookup)"""
        app_ids = self.find_nfd_app_ids_by_address(address)
        names = []
        if app_ids is not None:
            for app_id in app_ids:
                state = get_global_state(self.algod, app_id)
                names.append(NFDProperties(state).fetch_name())
        return names

    def lookup_name(self, nfd_name: str):
        app_id = self.find_nfd_app_id_by_name(nfd_name)
        properties = None
        if app_id is not None:
            state = get_global_state(self.algod, app_id)
            properties = NFDProperties(state).fetch_addresses()
        return properties


class NFDTestnetClient(NFDClient):
    def __init__(self, algod_client=None):
        if algod_client is None:
            algod_client = AlgodClient("", "https://testnet-api.algonode.cloud")
        super().__init__(
                algod_client,
                registry_app_id=TESTNET_REGISTRY_APP_ID,
                network="testnet"
        )


class NFDMainnetClient(NFDClient):
    def __init__(self, algod_client=None):
        if algod_client is None:
            algod_client = AlgodClient("", "https://mainnet-api.algonode.cloud")
        super().__init__(
                algod_client,
                registry_app_id=MAINNET_REGISTRY_APP_ID,
                network="mainnet"
        )
