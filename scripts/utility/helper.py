from brownie import (Contract, LinkToken, MockDAI, MockV3Aggregator, MockWETH,
                     accounts, config, network)
from brownie.network.account import LocalAccount
from brownie.network.transaction import TransactionReceipt

LOCAL_ENVIRONMENTS = [
    "development",
    "mainnet-fork"
]

contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "dai_usd_price_feed": MockV3Aggregator,
    "fau_token": MockDAI,
    "weth_token": MockWETH,
}

INITIAL_PRICE_FEED_VALUE = 2000000000000000000000
DECIMALS = 18


def get_account(index: int = None, id: str = None) -> LocalAccount:
    """
    Get account for operations.

    :param index: Index of the list of accounts.
    :type index: int
    :param id: ID of the account from keystore.
    :type id: str

    :return: Account to be used.
    :rtype: :class:`LocalAccount`
    """

    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if network.show_active() in LOCAL_ENVIRONMENTS:
        return accounts[0]
    if network.show_active() == "ganache-local":
        return accounts.add(config["wallets"]["local-ui"][0]["private_key"])

    return accounts.add(config["wallets"]["metamask"][0]["private_key"])


def get_contract(contract_name: str) -> Contract:
    """
    Get contract with name configured as *contract_name*.

    :param contract_name: Name of contract configured.
    :type contract_name: str

    :return: Contract of *contract_name*
    :rtype: :class:`Contract`
    """

    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active(
        )][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


def deploy_mocks(decimals: int = DECIMALS, initial_value: int = INITIAL_PRICE_FEED_VALUE) -> None:
    """
    Deploy mock conctracts for testing.

    :param decimals: Number of decimals in the price.
    :type decimals: int
    :param initial_value: Initial value of price feed.
    :type initial_value: int
    """

    print(f"The active network is {network.show_active()}")
    print("Deploying Mocks")
    account = get_account()
    print("Deploying Mock Link Token")
    link_token = LinkToken.deploy({"from": account})
    print(f"Deployed to {link_token.address}")
    print("Deploying Mock Price Feed")
    mock_price_feed = MockV3Aggregator.deploy(
        decimals, initial_value, {"from": account}
    )
    print(f"Deployed to {mock_price_feed.address}")
    print("Deploying Mock DAI")
    dai_token = MockDAI.deploy({"from": account})
    print(f"Deployed to {dai_token.address}")
    print("Deploying Mock WETH")
    weth_token = MockWETH.deploy({"from": account})
    print(f"Deployed to {weth_token.address}")


def fund_with_link(
        contract_address: str,
        account: LocalAccount = None,
        link_token: Contract = None,
        amount: int = 100000000000000000) -> TransactionReceipt:
    """
    Fund *contract_address* with some LINKs.

    :param contract_address: Contract address to be funded.
    :type contract_address: str
    :param account: Account to run transfer.
    :param account: :class:`LocalAccount`
    :type link_token: Contract of the LINK toiken.
    :type link_token: :class:`Contract`
    :type amount: Amount to be transferred.
    :type amount: int

    :return: Transaction of the LINK transfer.
    :rtype: :class:`TransactionReceipt`
    """

    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print("Funded contract with LINK")
    return tx


def is_verify_contract(network_name: str) -> bool:
    """
    Check if verify contract is required in *network_name*.

    :param network_name: Network name.
    :type network_name: str

    :return: True if verify contract.
    :rtype: bool
    """

    verify = (
        config["networks"][network_name]["verify"]
        if config["networks"][network_name].get("verify")
        else False
    )
    return verify
