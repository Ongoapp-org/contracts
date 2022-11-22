#!/usr/bin/python3

from brownie import accounts, network
from brownie import FTGStaking, MockFTGToken


def deploy_FTGStaking(tokenAddr):
    # account account "0x8E642F42f98A6bcD5E56afA845Eb7E21484DaE04" used for avax-test:
    if network.show_active() != "development":
        pk = "50cc9e6c3d47a3b4c3cb3eb611ad7d8c6eb5f1b1b1e54f61ef4d4582bfa77742"  # account "0x8E642F42f98A6bcD5E56afA845Eb7E21484DaE04"
        accounts.add(pk)

    print("account[0] in deploy_FTGStaking = ", accounts[0])
    print("balance ETH accounts[0] in deploy_FTGStaking =", accounts[0].balance())
    print("chain in deploy_FTGStaking=", network.chain)

    ftgstaking = FTGStaking.deploy(tokenAddr, {"from": accounts[0]})
    print("FTGStaking deployed at ", ftgstaking.address)
    return ftgstaking


def main():
    # Fetch the account
    # account = accounts[0]
    # pk1 = "b5f58344a9513b68d2f20435107de17d865b01d603f4558fef27c1fed071d8e2"
    pk2 = "c43766a57a118e09e3b4dcda38685d2b1bc6e0872af1f9e51dd4bd704d77abde"
    mainaccount = accounts.add(pk2)
    ftgmockAddress = "0xC54Aee27538ae906034e9f2f1A784778ab55d861"
    ftgmock = MockFTGToken.at(ftgmockAddress)
    print("mainaccount ", mainaccount)
    print("main FTG balance ", ftgmock.balanceOf(mainaccount) / 10**18)
    print("main ETH balance ", mainaccount.balance())
    # token = MockFTGToken.deploy(10 ** 9, {"from": mainaccount})

    # Deploy contract
    # deploy_FTGStaking()
    # Print contract address
    # print(f"contract deployed at {deploy_contract}")


""" 
def main(tokenAddr="0xB94738d2C57582830aC07ea8e513b58f49f6d321"): #default address = D1Token on AVAX-TESTNET
    deploy_BMarket(tokenAddr) """
