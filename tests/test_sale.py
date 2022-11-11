#!/usr/bin/python3
import brownie
from brownie import chain, network, FTGStaking, FTGSale, MockFTGToken
from scripts.deploy_FTGStaking import deploy_FTGStaking


def test_basicsale(accounts, pm, ftgtoken, investtoken):
    # for i in range(1, 3):
    #     assert ftgtoken.balanceOf(accounts[i]) == 10000
    # deploy the contract
    ftgstaking = deploy_FTGStaking(ftgtoken.address)
    ftgtoken.transfer(accounts[1], 100000000, {"from": accounts[0]})
    investtoken.transfer(accounts[1], 100000000, {"from": accounts[0]})

    assert investtoken.balanceOf(accounts[1]) == 100000000

    _amountGuaranteedPool = 1000000
    _amountPublicPool = 1000000
    _tokenPriceInUSD = 100
    MockFTGToken.deploy(30000000 * 10**18, {"from": accounts[0]})
    saletoken = ftgtoken
    #TODO
    #investtoken = ftgtoken

    owner = accounts[0]
    salectr = FTGSale.deploy("TestSale", investtoken ,saletoken, ftgstaking, _tokenPriceInUSD, {"from": owner})
    # print("accounts[0] = ", accounts[0])

    assert salectr.nameSale() == "TestSale"

    salectr.setMins(1000000, 500000, 250000, 100000)
    salectr.setAllocs(40, 30, 20, 10)
    salectr.setParticipants(1000, 500, 100, 50)

    #assert salectr.tiersMin(0) == 1000000
    print(salectr.tiersMin(0))
    print(type(salectr.tiersMin(0)))

    salectr.addWhitelist(accounts[1], {"from": owner})
    assert salectr.whitelist(accounts[1])
    
    days30 = 2592000
    ftgtoken.approve(ftgstaking, 100000, {"from": accounts[1]})
    ftgstaking.stake(100000, days30, {"from": accounts[1]})  

    #TODO
    #ae = salectr.amountEligible(accounts[1], {"from": accounts[1]}).call()
    #assert ae == 100

    #salectr.participate(100, {"from": accounts[1]})


    #salectr.Participants[accounts[1]].

    # assert salectr.amountGuaranteedPool() == 1000000
    # assert salectr.amountPublicPool() == 1000000

    #print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    #print("chain in test_FTGToken = ", network.chain)