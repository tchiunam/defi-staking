import json
import os
import shutil
from typing import Dict, Tuple

import yaml
from brownie import Contract, TokenFarm, TregonaiToken, network
from brownie.network.account import LocalAccount
from web3 import Web3

from scripts.utility.helper import (get_account, get_contract,
                                    is_verify_contract)

KEPT_BALANCE = Web3.toWei(100, "ether")


def deploy_token_and_farm(is_update_frontend: bool = False) -> Tuple:
    """
    Deploy our platform token and the token farm contract.

    :param update_frontend: True if update frontend configuration stored in
        another local git repo.
    :type update_frontend: bool

    :return: The deployed token and token farm contract.
    :rtype: Tuple
    """

    account = get_account()
    tregonai_token = TregonaiToken.deploy({"from": account})
    token_farm = TokenFarm.deploy(
        tregonai_token.address,
        {"from": account},
        publish_source=is_verify_contract(network_name=network.show_active()))
    tx = tregonai_token.transfer(
        token_farm.address,
        tregonai_token.totalSupply() - KEPT_BALANCE,
        {"from": account})
    tx.wait(1)
    weth_token = get_contract(contract_name="weth_token")
    fau_token = get_contract(contract_name="fau_token")
    allowed_tokens = {
        tregonai_token: get_contract("dai_usd_price_feed"),
        fau_token: get_contract("dai_usd_price_feed"),
        weth_token: get_contract("eth_usd_price_feed")
    }
    add_allowed_tokens(
        token_farm=token_farm,
        allowed_tokens=allowed_tokens,
        account=account)
    if is_update_frontend:
        update_frontend()
    return tregonai_token, token_farm


def add_allowed_tokens(token_farm: Contract, allowed_tokens: Dict, account: LocalAccount) -> None:
    """
    Add allowed tokens to *token_farm* contract.

    :param token_farm: Token farm contract.
    :type token_farm: :class:`Contract`
    :param allowed_tokens:  Mapping of token contract and price feed.
    :type allowed_tokens: Dict
    :param account: Account used to run this operation.
    :param account: :class:`LocalAccount`
    """

    for token in allowed_tokens:
        add_tx = token_farm.addAllowedToken(token.address, {"from": account})
        add_tx.wait(1)
        set_tx = token_farm.setPriceFeedContract(
            token.address,
            allowed_tokens[token],
            {"from": account})
        set_tx.wait(1)


def update_frontend():
    """
    Update frontend with the latest brownie config. This is a quick way assuming that
    frontend files is located in a local repository.
    """

    with open("brownie-config.yaml", "r") as brownie_config:
        copy_folders_to_frontend(
            "./build", "../defi-staking-frontend/src/chain-info")
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        # This is just a quick way ot managing shared data between repo for this exercise.
        # Some kind of deployment storage needs to be in place if a proper design is needed.
        with open("../defi-staking-frontend/src/brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)


def copy_folders_to_frontend(source: str, destination: str):
    """
    Copy a folder from *source* to *destination*.

    :param source: Source folder.
    :type source: str
    :param destination: Destination folder.
    :type destination: str
    """

    if os.path.exists(destination):
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def main():
    deploy_token_and_farm(is_update_frontend=True)
