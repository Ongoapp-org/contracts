#!/usr/bin/python3
import brownie
from brownie import chain, network, FTGStaking, FTGSale
from scripts.deploy_FTGStaking import deploy_FTGStaking


def test_basicsale(accounts, pm, ftgtoken):
    # for i in range(1, 3):
    #     assert ftgtoken.balanceOf(accounts[i]) == 10000
    # deploy the contract
    ftgstaking = deploy_FTGStaking(ftgtoken.address)
    _amountGuaranteedPool = 1000000
    _amountPublicPool = 1000000
    _tokenPriceInUSD = 100
    salectr = FTGSale.deploy("TestSale",ftgstaking, _amountGuaranteedPool, _amountPublicPool, _tokenPriceInUSD, {"from": accounts[0]})
    print("accounts[0] = ", accounts[0])

    assert salectr.saleName() == "TestSale"
    assert salectr.amountGuaranteedPool() == 1000000
    assert salectr.amountPublicPool() == 1000000

    #print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    #print("chain in test_FTGToken = ", network.chain)