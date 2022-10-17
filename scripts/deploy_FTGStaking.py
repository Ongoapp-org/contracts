#!/usr/bin/python3

from brownie import FTGStaking, accounts, network

def deploy_FTGStaking(tokenAddr):
    # account account "0x8E642F42f98A6bcD5E56afA845Eb7E21484DaE04" used for avax-test:
    if network.show_active() != "development":
        pk = "50cc9e6c3d47a3b4c3cb3eb611ad7d8c6eb5f1b1b1e54f61ef4d4582bfa77742" #account "0x8E642F42f98A6bcD5E56afA845Eb7E21484DaE04"
        accounts.add(pk)

    print("account[0] in deploy_FTGStaking = ", accounts[0])
    print("balance ETH accounts[0] in deploy_FTGStaking =", accounts[0].balance())
    print("chain in deploy_FTGStaking=", network.chain)
        
    ftgstaking = FTGStaking.deploy(tokenAddr,{"from": accounts[0]})
    print("FTGStaking deployed at ", ftgstaking.address)
    return ftgstaking
""" 
def main(tokenAddr="0xB94738d2C57582830aC07ea8e513b58f49f6d321"): #default address = D1Token on AVAX-TESTNET
    deploy_BMarket(tokenAddr) """