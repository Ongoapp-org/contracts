#!/usr/bin/python3

from brownie import accounts, network, chain
from brownie import FTGStaking, MockFTGToken


def deploy_local():
    ftgmockAddress = MockFTGToken.deploy(10 ** 9 * 10**18, {"from": accounts[0]})
    print("ftgmock ", ftgmockAddress)

    ftgstaking = FTGStaking.deploy(ftgmockAddress, {"from": accounts[0]})
    print("FTGStaking deployed at ", ftgstaking.address)

    ftgmock = MockFTGToken.at(ftgmockAddress)    
    bal = ftgmock.balanceOf(accounts[0])
    ftgmock.transfer(accounts[1], 1000 * 10**18, {"from": accounts[0]})

    ftgstaking.depositRewardTokens(1000 * 10**18, {"from": accounts[0]})

    return [ftgmock, ftgstaking]


def run_staketest(ftgmock, ftgstaking):
    ftgmock.approve(ftgstaking, 100*10**18,{"from": accounts[1]})
    days30 = 60*60*24*30
    #ftgstaking.stake(100*10**18, 10, {"from":accounts[0]})
    ftgstaking.stake(100*10**18, days30, {"from":accounts[1]})
    #ftgstaking.stakeholders(accounts[0])

    print("time before ", chain.time())
    chain.sleep(days30+1)
    print("time after ", chain.time())
    #chain.mine()
    # print("time after ",chain.time())
    #print(ftgstaking.getBalances(accounts[1])[0])
    ftgstaking.updateBalances(accounts[1])
    print(ftgstaking.stakeholders(accounts[1]))
    #print(ftgstaking.withdrawableAmount({"from":accounts[1]}))
    ftgstaking.unstake(95*10**18, {"from":accounts[1]}) 
    print(ftgstaking.stakeholders(accounts[1]))
    print(ftgmock.balanceOf(accounts[1]))


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
    print("main FTG balance ", ftgmock.balanceOf(mainaccount) / 10**18)
    print("main ETH balance ", mainaccount.balance()/10**18)

    ftgstaking = FTGStaking.deploy(ftgmockAddress, {"from": mainaccount})
    print("staking deployed at ", ftgstaking)


def main():
    
    #testnet
    if network.chain.id == 1337:
        [ftgmock, ftgstaking] = deploy_local()
        print(ftgmock, ftgstaking)
        run_staketest(ftgmock, ftgstaking)


    # if network.chain.id == 5:
    #     deploy_goerli()

    #     #print("FTGStaking deployed at ", staking.address)


