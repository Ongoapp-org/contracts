#!/usr/bin/python3

from brownie import accounts, network, chain
from brownie import FTGStaking, MockFTGToken


def deploy_FTGStaking(tokenAddr, mainaccount):
    # account account "0x8E642F42f98A6bcD5E56afA845Eb7E21484DaE04" used for avax-test:
    # if network.show_active() != "development":
    #     pk = "50cc9e6c3d47a3b4c3cb3eb611ad7d8c6eb5f1b1b1e54f61ef4d4582bfa77742"  # account "0x8E642F42f98A6bcD5E56afA845Eb7E21484DaE04"
    #     accounts.add(pk)

    print("account[0] in deploy_FTGStaking = ", mainaccount)
    print("balance ETH accounts[0] in deploy_FTGStaking =", mainaccount.balance())
    print("chain in deploy_FTGStaking=", network.chain)

    ftgstaking = FTGStaking.deploy(tokenAddr, {"from": mainaccount})
    return ftgstaking


def deploy_goerli():
    print("goerli")
    # Fetch the account
    # account = accounts[0]
    # pk1 = "b5f58344a9513b68d2f20435107de17d865b01d603f4558fef27c1fed071d8e2"
    pk2 = "c43766a57a118e09e3b4dcda38685d2b1bc6e0872af1f9e51dd4bd704d77abde"
    mainaccount = accounts.add(pk2)
    ftgmockAddress = "0xC54Aee27538ae906034e9f2f1A784778ab55d861"
    ftgmock = MockFTGToken.at(ftgmockAddress)
    print("mainaccount ", mainaccount)
    print("main FTG balance ", ftgmock.balanceOf(mainaccount) / 10 ** 18)
    print("main ETH balance ", mainaccount.balance() / 10 ** 18)

    ftgstaking = FTGStaking.deploy(ftgmockAddress, {"from": mainaccount})
    print("staking deployed at ", ftgstaking)


def main():
    print("chain_id =", network.chain.id)
    if network.chain.id == 1337:
        ftgmockAddress = MockFTGToken.deploy(10 ** 9 * 10 ** 18, {"from": accounts[0]})
        print("ftgmock ", ftgmockAddress)

        staking = deploy_FTGStaking(ftgmockAddress, accounts[0])
        print("FTGStaking deployed at ", staking.address)
    elif network.chain.id == 5:
        deploy_goerli()
