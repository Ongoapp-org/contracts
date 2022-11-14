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
    
    saletoken = MockFTGToken.deploy(30_000_000 * 10**18, {"from": accounts[0]})
    assert saletoken.balanceOf(accounts[0]) == 30_000_000 * 10**18
    #saletoken = ftgtoken
    #TODO
    #investtoken = ftgtoken

    owner = accounts[0]
    _totalTokensToSell = 10_000_000
    _totalToRaise = 100_000
    _tokenPriceInUSD = 100 #_totalTokensToSell/_totalToRaise

    salectr = FTGSale.deploy("TestSale", investtoken ,saletoken, ftgstaking, _tokenPriceInUSD, _totalTokensToSell, _totalToRaise, {"from": owner})
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
    stakeAmount = 1100000
    ftgtoken.approve(ftgstaking, stakeAmount, {"from": accounts[1]})
    ftgstaking.stake(stakeAmount, days30, {"from": accounts[1]})  

    #TODO
    #uint256 amountLocked = uint(IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(account, 30 days));
    # calculate init staking fee
    amountlocked = ftgstaking.checkParticipantLockedStaking(accounts[1], days30)
    assert amountlocked == stakeAmount * (1-0.05)    

    #assert salectr.allocTotal(3) == 100
    assert salectr.allocTotal(0) == 0
    assert salectr.allocTotal(1) == 40
    assert salectr.tiersParticipants(1) == 1000
    assert salectr.tiersParticipants(4) == 50

    #allocTotal[Tiers.RUBY] / tiersParticipants[Tiers.RUBY]

    assert stakeAmount > salectr.tiersMin(3) 
    assert amountlocked > salectr.tiersMin(3) 
    
    assert salectr.allocTotal(1) / salectr.tiersParticipants(1) == 40/1000
    #TODO
    #ae = salectr.amountEligible(accounts[1], {"from": accounts[1]})
    assert salectr.totalTokensToSell() == _totalTokensToSell
    assert salectr.tokensSold() == 0

    saletoken.transfer(salectr, _totalTokensToSell, {"from": accounts[0]})
    assert investtoken.balanceOf(accounts[1]) >= _totalTokensToSell
    investtoken.approve(salectr, 100, {"from": accounts[1]})
    salectr.participate(100, {"from": accounts[1]})

    #assert ae == totalTokensSold * 40/1000 /10000
    assert salectr.tokensSold() == 100
    assert salectr.investRaised() == 1

    #assert salectr.participants(accounts[1]).tokensBought == 100
    #assert salectr.participants(accounts[1]).amountInvested == 1

    assert salectr.participants(accounts[1]) == (1, 100)

    

    # assert salectr.amountGuaranteedPool() == 1000000
    # assert salectr.amountPublicPool() == 1000000

    #print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    #print("chain in test_FTGToken = ", network.chain)