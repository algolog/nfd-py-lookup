from logging import getLogger
from base64 import b64encode, b64decode
from algosdk.v2client.algod import AlgodClient
from algosdk.error import AlgodHTTPError
from algosdk.encoding import decode_address, encode_address
from algosdk.logic import get_application_address
from .constants import TESTNET_REGISTRY_APP_ID, MAINNET_REGISTRY_APP_ID
from .contracts import (
    get_nfd_name_logicsig,
    get_nfd_revaddress_logicsig,
    get_registry_box_name_for_nfd,
    get_registry_box_name_for_address,
)
from .nfdproperties import NFDProperties
from .utils import unpack_uints, get_global_state, get_app_info_bytes, get_application_boxes


logger = getLogger(__name__)


class NFDClient:
    def __init__(self, algod_client: AlgodClient, registry_app_id: int, network: str):
        self.algod = algod_client
        self.registry_app_id = registry_app_id
        self.network = network

    def find_nfd_app_id_by_name(self, nfd_name: str):
        app_id = None
        try:
            # First try to resolve via V2
            box = self.algod.application_box_by_name(
                self.registry_app_id, get_registry_box_name_for_nfd(nfd_name)
            )
            box_value = b64decode(box["value"])
            # The box data is stored as {ASA ID}{APP ID} - packed 64-bit ints
            if len(box_value) != 16:
                raise ValueError(
                    f"box data is invalid - {len(box_value)=} but should be 16 for {nfd_name=}"
                )
            app_id = int.from_bytes(box_value[8:], "big")
            logger.debug(f"Found as V2 name, appID: {app_id}")
        except AlgodHTTPError:
            # Fall back to V1 approach
            lsig = get_nfd_name_logicsig(nfd_name, self.registry_app_id)
            address = lsig.address()
            logger.debug(f"V1 LSIG address used: {address}")
            try:
                info = self.algod.account_application_info(address, self.registry_app_id)
                # We found our registry contract in the local state of the account
                app_id = int.from_bytes(get_app_info_bytes(info, "i.appid"), "big")
                logger.debug(f"Found as V1 name, appID: {app_id}")
            except AlgodHTTPError:
                return None
        return app_id

    def find_nfd_app_ids_by_address(self, lookup_address: str) -> list[int]:
        app_ids = None
        b_address = decode_address(lookup_address)
        # First try to resolve via V2
        try:
            box = self.algod.application_box_by_name(
                self.registry_app_id, get_registry_box_name_for_address(b_address)
            )
            box_value = b64decode(box["value"])
            # Get the set of nfd app ids referenced by this address - we just grab the first for now
            app_ids = unpack_uints(box_value)
            logger.debug(f"Found {len(app_ids)} NFDs linked as V2 address")
        except AlgodHTTPError:
            # TODO: check that error was 404 - Not Found
            # fall back to V1 approach
            lsig = get_nfd_revaddress_logicsig(
                encode_address(b_address), self.registry_app_id
            )
            address = lsig.address()
            logger.debug(f"V1 LSIG rev-address used: {address}")
            try:
                # Read the local state for our registry SC from this specific account
                info = self.algod.account_application_info(address, self.registry_app_id)
                # We found our registry contract in the local state of the account
                app_ids = []
                for idx in range(16):
                    this_key_ids = unpack_uints(get_app_info_bytes(info, f"i.apps{idx}"))
                    if not this_key_ids:
                        break
                    app_ids.extend(this_key_ids)
                logger.debug(f"Found {len(app_ids)} NFDs linked as V1 address")
            except AlgodHTTPError:
                return None
        return app_ids

    def lookup_address(self, address: str) -> list[str]:
        """Return list of names associated with address (reverse lookup)"""
        app_ids = self.find_nfd_app_ids_by_address(address)
        names = []
        if app_ids is not None:
            for app_id in app_ids:
                # Load the global state of this NFD
                state = get_global_state(self.algod, app_id)
                # Now load all the box data (V2)
                box_data = get_application_boxes(self.algod, app_id)
                names.append(NFDProperties(state, box_data).fetch_name())
        return names

    def lookup_name(self, nfd_name: str) -> dict:
        """Return addresses associated with the NFD name"""
        app_id = self.find_nfd_app_id_by_name(nfd_name)
        properties = None
        if app_id is not None:
            # Load the global state of this NFD
            state = get_global_state(self.algod, app_id)
            # Now load all the box data (V2)
            box_data = get_application_boxes(self.algod, app_id)
            properties = NFDProperties(state, box_data).fetch_addresses()
            logger.debug(f"Vault address for {nfd_name}: {get_application_address(app_id)}")
        return properties

    def lookup_opted_and_owned_by(self, address: str) -> list[str]:
        """Return list of NFDs both opted-in and owned by address"""
        account_assets = self.algod.account_info(address).get("assets", [])
        names = []
        for asset in account_assets:
            try:
                asset_info = self.algod.asset_info(asset["asset-id"])
            except AlgodHTTPError:
                continue
            params = asset_info["params"]
            if (
                params.get("unit-name") == "NFD"
                and params.get("decimals") == 0
                and params.get("total") == 1
                # assume that NFD name fits into ASA name (not always the case)
                and self.lookup_name(params["name"]).get("i.owner.a") == address
            ):
                names.append(params["name"])
        return names


class NFDTestnetClient(NFDClient):
    def __init__(self, algod_client=None):
        if algod_client is None:
            algod_client = AlgodClient("", "https://testnet-api.algonode.cloud")
        super().__init__(
            algod_client, registry_app_id=TESTNET_REGISTRY_APP_ID, network="testnet"
        )


class NFDMainnetClient(NFDClient):
    def __init__(self, algod_client=None):
        if algod_client is None:
            algod_client = AlgodClient("", "https://mainnet-api.algonode.cloud")
        super().__init__(
            algod_client, registry_app_id=MAINNET_REGISTRY_APP_ID, network="mainnet"
        )
