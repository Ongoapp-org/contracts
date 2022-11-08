#!/usr/bin/python3
import brownie
from brownie import chain, network, FTGStaking, FTGSale, MockFTGToken
from scripts.deploy_FTGStaking import deploy_FTGStaking


def test_basicsale(accounts, pm, ftgtoken):
    # for i in range(1, 3):
    #     assert ftgtoken.balanceOf(accounts[i]) == 10000
    # deploy the contract
    ftgstaking = deploy_FTGStaking(ftgtoken.address)
    _amountGuaranteedPool = 1000000
    _amountPublicPool = 1000000
    _tokenPriceInUSD = 100
    MockFTGToken.deploy(30000000 * 10**18, {"from": accounts[0]})
    saletoken = ftgtoken
    investtoken = ftgtoken
    salectr = FTGSale.deploy("TestSale", investtoken ,saletoken, ftgstaking, _tokenPriceInUSD, {"from": accounts[0]})
    # print("accounts[0] = ", accounts[0])

    assert salectr.nameSale() == "TestSale"

    salectr.setMins(1000000, 500000, 250000, 100000)
    salectr.setAllocs(40, 30, 20, 10)
    salectr.setParticipants(1000, 500, 100, 50)

    assert salectr.tiersMin[0] == 1000000

    # assert salectr.amountGuaranteedPool() == 1000000
    # assert salectr.amountPublicPool() == 1000000

    #print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    #print("chain in test_FTGToken = ", network.chain)