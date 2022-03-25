from typing import Tuple

import pytest
from brownie import Contract, exceptions, network
from brownie.network.account import LocalAccount
from scripts.deploy import deploy_token_and_farm
from scripts.utility.helper import (INITIAL_PRICE_FEED_VALUE,
                                    LOCAL_ENVIRONMENTS, get_account,
                                    get_contract)


def test_set_price_feed_contract():
    if network.show_active() not in LOCAL_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account: LocalAccount = get_account()
    non_owner_account: LocalAccount = get_account(index=1)
    tregonai_token: Contract
    token_farm: Contract
    tregonai_token, token_farm = deploy_token_and_farm()
    price_feed_address = get_contract("eth_usd_price_feed")
    token_farm.setPriceFeedContract(
        tregonai_token,
        price_feed_address,
        {"from": account})
    assert token_farm.tokenPriceFeedMapping(
        tregonai_token.address) == price_feed_address
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setPriceFeedContract(
            tregonai_token,
            price_feed_address,
            {"from": non_owner_account})


def test_stake_tokens(amount_staked) -> Tuple[Contract, Contract]:
    if network.show_active() not in LOCAL_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account: LocalAccount = get_account()
    tregonai_token, token_farm = deploy_token_and_farm()
    tregonai_token.approve(
        token_farm.address,
        amount_staked,
        {"from": account})
    token_farm.stakeToken(amount_staked, tregonai_token, {"from": account})
    assert token_farm.stakingBalance(
        tregonai_token.address, account.address) == amount_staked
    assert token_farm.uniqueTokensStaked(account.address) == 1
    assert token_farm.stakers(0) == account.address

    return tregonai_token, token_farm


def test_issue_tokens(amount_staked):
    if network.show_active() not in LOCAL_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account: LocalAccount = get_account()
    tregonai_token, token_farm = test_stake_tokens(amount_staked)
    starting_balance = tregonai_token.balanceOf(account.address)
    token_farm.issueTokens({"from": account})
    assert tregonai_token.balanceOf(
        account.address) == starting_balance + INITIAL_PRICE_FEED_VALUE
