#!/usr/bin/python3
import pytest
import brownie
from brownie import chain, network, FTGAirdrop, accounts
from scripts.deploy_FTGStaking import deploy_FTGStaking


@pytest.fixture(scope="module", autouse=True)
def ftgstaking(accounts, ftgtoken):
    # ftgstaking deployment
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    return ftgstaking


@pytest.fixture(scope="module", autouse=True)
def airdroptoken(MockFTGToken, accounts):
    print("airdroptoken deployment by accounts[0]=", accounts[0])
    return MockFTGToken.deploy(1_000_000 * 10 ** 18, {"from": accounts[0]})


@pytest.fixture(scope="module", autouse=True)
def ftgairdrop(accounts, airdroptoken, ftgstaking):
    totalTokensToAirdrop = 1_000_000
    ftgairdrop = FTGAirdrop.deploy(
        airdroptoken, ftgstaking, totalTokensToAirdrop, {"from": accounts[0]}
    )
    return ftgairdrop


def test_setup_phase(accounts, ftgairdrop, airdroptoken, ftgtoken):
    print("********************Setup Phase Tests********************")
    # airdrop eligible locked staking duration
    eligibleLockDuration = 3600 * 24 * 30  # one month
    ftgairdrop.setEligibleLockDuration(eligibleLockDuration)
    assert ftgairdrop.eligibleLockDuration() == eligibleLockDuration
