#!/usr/bin/python3
import brownie
from brownie import chain, network, FTGStaking, FTGSale, MockFTGToken, NRT
from scripts.deploy_FTGStaking import deploy_FTGStaking


def test_basicsale(accounts, pm, ftgtoken, investtoken):

    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    ftgtoken.transfer(accounts[1], 10_000_000 * 10 ** 18, {"from": accounts[0]})
    ftgtoken.transfer(accounts[2], 500_000 * 10 ** 18, {"from": accounts[0]})

    assert investtoken.balanceOf(accounts[0]) == 30_000_000 * 10 ** 18

    investtoken.transfer(accounts[1], 10_000_000 * 10 ** 18, {"from": accounts[0]})
    investtoken.transfer(accounts[2], 1_000_000 * 10 ** 18, {"from": accounts[0]})

    assert investtoken.balanceOf(accounts[1]) == 10_000_000 * 10 ** 18
    assert investtoken.balanceOf(accounts[2]) == 1_000_000 * 10 ** 18

    _totalTokensToSell = 10_000_000 * 10 ** 18
    _totalToRaise = 100_000 * 10 ** 18
    # 0.01
    _tokenPriceInUSD = 1 * 10 ** 16
    # TODO
    # assert _totalTokensToSell * _tokenPriceInUSD/10**18 == _totalToRaise
    # assert int(_totalTokensToSell/100) == int(_totalToRaise)

    nrt = NRT.deploy("NRT", 18, {"from": accounts[0]})

    salectr = FTGSale.deploy(
        nrt,
        investtoken,
        ftgstaking,
        _tokenPriceInUSD,
        _totalTokensToSell,
        _totalToRaise,
        {"from": accounts[0]},
    )

    nrt.addOwner(salectr, {"from": accounts[0]})

    assert salectr.salePhase() == 0

    # setup sale

    NONE = 0
    RUBY = 1
    EMERALD = 2
    SAPPHIRE = 3
    DIAMOND = 4

    day1 = 60 * 60 * 24
    salectr.setPhasesDurations(day1, day1, day1)
    RUBY_MIN = 100_000
    EMERALD_MIN = 250_000
    SAPPHIRE_MIN = 500_000
    DIAMOND_MIN = 1_000_000
    salectr.setTiersMinFTGStakings(RUBY_MIN, EMERALD_MIN, SAPPHIRE_MIN, DIAMOND_MIN)

    assert salectr.tiersMinFTGStaking(NONE) == 0
    assert salectr.tiersMinFTGStaking(RUBY) == 100_000
    assert salectr.tiersMinFTGStaking(EMERALD) == 250_000
    assert salectr.tiersMinFTGStaking(SAPPHIRE) == 500_000
    assert salectr.tiersMinFTGStaking(DIAMOND) == 1_000_000

    salectr.setTiersTokensAllocationFactors(2, 4, 8, {"from": accounts[0]})
    assert salectr.tiersTokensAllocationFactor(RUBY) == 1
    assert salectr.tiersTokensAllocationFactor(SAPPHIRE) == 2
    assert salectr.tiersTokensAllocationFactor(EMERALD) == 4
    assert salectr.tiersTokensAllocationFactor(DIAMOND) == 8

    salectr.launchNextPhase({"from": accounts[0]})

    # register phase
    assert salectr.salePhase() == 1

    days30 = 2592000
    stakeAmount = 1_100_000
    ftgtoken.approve(ftgstaking, stakeAmount, {"from": accounts[1]})
    ftgstaking.stake(stakeAmount, days30, {"from": accounts[1]})

    salectr.registerForSale({"from": accounts[1]})

    assert salectr.participants(accounts[1]) == (0, 0, True, DIAMOND)

    days30 = 2592000
    stakeAmount = 110_000
    ftgtoken.approve(ftgstaking, stakeAmount, {"from": accounts[2]})
    ftgstaking.stake(stakeAmount, days30, {"from": accounts[2]})

    salectr.registerForSale({"from": accounts[2]})

    assert salectr.participants(accounts[2]) == (0, 0, True, RUBY)

    assert salectr.tiersNbOFParticipants(RUBY) == 1
    assert salectr.tiersNbOFParticipants(DIAMOND) == 1

    assert salectr.checkTierEligibility(accounts[1]) == DIAMOND
    assert salectr.checkTierEligibility(accounts[2]) == RUBY

    timeTravel = day1 + 60 * 60
    chain.sleep(timeTravel)

    salectr.launchNextPhase({"from": accounts[0]})

    # guaranteed phase
    assert salectr.salePhase() == 2

    bamount = 100 * 10 ** 18

    assert investtoken.balanceOf(accounts[1]) == 10_000_000 * 10 ** 18

    investtoken.approve(salectr, bamount, {"from": accounts[1]})
    salectr.buytoken(bamount, {"from": accounts[1]})

    assert nrt.balanceOf(accounts[1]) == bamount

    # how much can buy?
    assert salectr.n() == 1111111111111111111111111111111111

    # TODO test cant buy more than diamond

    # ruby cant buy?
    bamount = 100 * 10 ** 18

    investtoken.approve(salectr, bamount, {"from": accounts[2]})
    salectr.buytoken(bamount, {"from": accounts[2]})

    # investAmount = 10_000
    # buyTokenamount = investAmount/ (_tokenPriceInUSD/10**18)

    # investtoken.approve(salectr, investAmount*10, {"from": accounts[2]})
    # assert investtoken.allowance(accounts[2], salectr) == investAmount*10
    # #TODO should fail
    # with brownie.reverts():
    #     salectr.buytoken(buyTokenamount, {"from": accounts[2]})

    ##### public phase

    timeTravel = day1 + 60 * 60
    chain.sleep(timeTravel)

    salectr.launchNextPhase({"from": accounts[0]})
    assert salectr.salePhase() == 3

    investAmount = 1_000
    buyTokenamount = investAmount / (_tokenPriceInUSD / 10 ** 18)

    assert buyTokenamount == 100_000

    investtoken.approve(salectr, investAmount, {"from": accounts[2]})
    assert investtoken.allowance(accounts[2], salectr) == investAmount
    salectr.buytoken(buyTokenamount, {"from": accounts[2]})

    ##### completed phase

    salectr.launchNextPhase({"from": accounts[0]})
    assert salectr.salePhase() == 4

    investtoken.approve(salectr, investAmount, {"from": accounts[2]})
    with brownie.reverts():
        salectr.buytoken(buyTokenamount, {"from": accounts[2]})
        # assert investtoken.allowance(accounts[2], salectr) == investAmount

    # salectr.launchNextPhase({"from": accounts[0]})

    # investtoken.approve(salectr, bamount, {"from": accounts[1]})
    # alectr.buytoken(bamount, {"from": accounts[1]})

    # investtoken.approve(salectr, bamount, {"from": accounts[2]})
    # salectr.buytoken(bamount, {"from": accounts[1]})

    # saletoken = MockFTGToken.deploy(30_000_000 * 10**18, {"from": accounts[0]})
    # saletoken.transfer(accounts[1], 10_000_000 * 10**18, {"from": accounts[0]})
    # saletoken.transfer(accounts[2], 1_000_000 * 10**18, {"from": accounts[0]})
    # assert saletoken.balanceOf(accounts[0]) == 19_000_000 * 10**18
    # assert saletoken.balanceOf(accounts[1]) == 10_000_000 * 10**18
    # assert saletoken.balanceOf(accounts[2]) == 1_000_000 * 10**18

    ############ old

    # salectr.registerForSale({"from": accounts[2]})

    # print("accounts[0] = ", accounts[0])

    # saectr.setMins(1000000, 500000, 250000, 100000)
    # salectr.setAllocs(40, 30, 20, 10)
    # salectr.setParticipants(1000, 500, 100, 50)

    # # assert salectr.tiersMin(0) == 1000000
    # print(salectr.tiersMin(0))
    # print(type(salectr.tiersMin(0)))

    # salectr.addWhitelist(accounts[1], {"from": owner})
    # assert salectr.participants(accounts[1]) == (0, 0, True)

    # # TODO
    # # uint256 amountLocked = uint(IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(account, 30 days));
    # # calculate init staking fee
    # amountlocked = ftgstaking.checkParticipantLockedStaking(accounts[1], days30)
    # assert amountlocked == stakeAmount * (1 - 0.05)

    # # allocTotal[Tiers.RUBY] / tiersParticipants[Tiers.RUBY]

    # assert stakeAmount > salectr.tiersMin(3)
    # assert amountlocked > salectr.tiersMin(3)

    # assert salectr.tiersTotal(1) / salectr.tiersParticipants(1) == 40 / 1000
    # # TODO
    # ae = salectr.amountEligible(accounts[1], {"from": accounts[1]})
    # assert ae == 1000 * 0.4 * _totalTokensToSell
    # assert salectr.totalTokensToSell() == _totalTokensToSell
    # assert salectr.tokensSold() == 0

    # saletoken.transfer(salectr, _totalTokensToSell, {"from": accounts[0]})
    # assert investtoken.balanceOf(accounts[1]) >= _totalTokensToSell
    # investtoken.approve(salectr, 100, {"from": accounts[1]})
    # salectr.participate(100, {"from": accounts[1]})

    # # assert ae == totalTokensSold * 40/1000 /10000
    # assert salectr.tokensSold() == 100
    # assert salectr.investRaised() == 1

    # # assert salectr.participants(accounts[1]).tokensBought == 100
    # # assert salectr.participants(accounts[1]).amountInvested == 1

    # assert salectr.participants(accounts[1]) == (1, 100)

    # assert salectr.amountGuaranteedPool() == 1000000
    # assert salectr.amountPublicPool() == 1000000

    # print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    # print("chain in test_FTGToken = ", network.chain)
