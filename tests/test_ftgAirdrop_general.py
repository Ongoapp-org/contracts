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
    totalTokensToAirdrop = 1_000_000 * 10 ** 18
    ftgairdrop = FTGAirdrop.deploy(
        airdroptoken, ftgstaking, totalTokensToAirdrop, {"from": accounts[0]}
    )
    return ftgairdrop


def participants_stakings(ftgtoken, ftgstaking):
    staking0 = 530_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking0, {"from": accounts[0]})
    ftgstaking.stake(staking0, 5184000, {"from": accounts[0]})
    staking1 = 1_100_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking1, {"from": accounts[1]})
    ftgstaking.stake(staking1, 2592000, {"from": accounts[1]})
    staking2 = 110_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking2, {"from": accounts[2]})
    ftgstaking.stake(staking2, 3000000, {"from": accounts[2]})
    staking3 = 160_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking3, {"from": accounts[3]})
    ftgstaking.stake(staking3, 6000000, {"from": accounts[3]})
    staking4 = 265_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking4, {"from": accounts[4]})
    ftgstaking.stake(staking4, 2592000, {"from": accounts[4]})


@pytest.fixture
def participants_preparation(ftgtoken, ftgstaking):
    # participants prepare for sale participation
    return participants_stakings(ftgtoken, ftgstaking)


def test_airdrop_1(
    accounts, ftgairdrop, participants_preparation, airdroptoken, ftgtoken
):
    print("********************Airdrop Test 1********************")
    # airdrop eligible locked staking duration
    eligibleLockDuration = 3600 * 24 * 45  # one month and half
    ftgairdrop.setEligibleLockDuration(eligibleLockDuration)
    assert ftgairdrop.eligibleLockDuration() == eligibleLockDuration
    # send airdropTokens to airdrop contract
    airdroptoken.transfer(ftgairdrop, 1_000_000 * 10 ** 18, {"from": accounts[0]})
    # airdrop for initial stakers
    tx = ftgairdrop.launchAirdrop()
    print(tx.events)
    # verification of expected airdrops made
    assert ftgairdrop.totalTokensToAirdrop() == 1_000_000 * 10 ** 18
    # for accounts[3]:
    eligibleActiveStakingLocked3 = 160_000 * 10 ** 18
    ftgairdrop.totalTokensToAirdrop() == 1_000_000 * 10 ** 18
    totalEligibleActiveStakingLocked = 530_000 * 10 ** 18 + 160_000 * 10 ** 18
    assert "{:.15e}".format(airdroptoken.balanceOf(accounts[3])) == "{:.15e}".format(
        eligibleActiveStakingLocked3
        * ftgairdrop.totalTokensToAirdrop()
        / totalEligibleActiveStakingLocked
    )
    # more tests with time travel and more stakings coming...
