#!/usr/bin/python3
import pytest
import brownie
from brownie import chain, network, FTGSale
from scripts.deploy_FTGStaking import deploy_FTGStaking


@pytest.fixture(scope="module", autouse=True)
def nrt(accounts, NRT):
    # accounts[0] deploys NRT contract
    nrt = NRT.deploy("NRT", 18, {"from": accounts[0]})
    return nrt


@pytest.fixture(scope="module", autouse=True)
def ftgsale(accounts, nrt, ftgtoken, investtoken):

    # ftgstaking deployment
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])

    # FTGSale deployment
    _totalTokensToSell = 10_000_000
    _totalToRaise = 100_000 * 10 ** 18
    # token price = 0.01 investToken
    _tokenPrice = int(_totalToRaise / _totalTokensToSell)
    print("_tokenPrice = ", _tokenPrice)
    # accounts[0] deploys FTGSale contract
    ftgsale = FTGSale.deploy(
        nrt,
        investtoken,
        ftgstaking,
        _tokenPrice,
        _totalTokensToSell,
        _totalToRaise,
        {"from": accounts[0]},
    )
    return ftgsale


def test_setup_phase(ftgsale, nrt, accounts, ftgtoken, investtoken):
    # verifies that we are in setup phase of the sale
    assert ftgsale.salePhase() == 0
    # Tiers enum codes
    NONE = 0
    RUBY = 1
    EMERALD = 2
    SAPPHIRE = 3
    DIAMOND = 4
    # TODO tests of right phase?
    # TODO tests of revert if not owner

    # definition of Sale's Phases durations
    phaseDuration = 86400  # one day
    ftgsale.setPhasesDurations(phaseDuration, phaseDuration, phaseDuration)
    # definition of Tiers minimum ftg locked staking
    RUBY_MIN = 100_000 * 10 ** 18
    EMERALD_MIN = 250_000 * 10 ** 18
    SAPPHIRE_MIN = 500_000 * 10 ** 18
    DIAMOND_MIN = 1_000_000 * 10 ** 18
    ftgsale.setTiersMinFTGStakings(RUBY_MIN, EMERALD_MIN, SAPPHIRE_MIN, DIAMOND_MIN)
    assert ftgsale.tiersMinFTGStaking(NONE) == 0
    assert ftgsale.tiersMinFTGStaking(RUBY) == 100_000 * 10 ** 18
    assert ftgsale.tiersMinFTGStaking(EMERALD) == 250_000 * 10 ** 18
    assert ftgsale.tiersMinFTGStaking(SAPPHIRE) == 500_000 * 10 ** 18
    assert ftgsale.tiersMinFTGStaking(DIAMOND) == 1_000_000 * 10 ** 18
    # definition of tiers allocation factors
    ftgsale.setTiersTokensAllocationFactors(2, 4, 8, {"from": accounts[0]})
    assert ftgsale.tiersTokensAllocationFactor(RUBY) == 1
    assert ftgsale.tiersTokensAllocationFactor(SAPPHIRE) == 2
    assert ftgsale.tiersTokensAllocationFactor(EMERALD) == 4
    assert ftgsale.tiersTokensAllocationFactor(DIAMOND) == 8
    # test if factors are not in ascendant order
    with brownie.reverts("factors must be increasing from lower to higher tiers"):
        ftgsale.setTiersTokensAllocationFactors(3, 2, 8, {"from": accounts[0]})
    # admin launch the next phase
    ftgsale.launchNextPhase({"from": accounts[0]})
    assert ftgsale.salePhase() == 1
    # verification that we cannot anymore access the setup functions
    with brownie.reverts("not setup phase"):
        phaseDuration = 86400 * 2  # one day
        ftgsale.setPhasesDurations(phaseDuration, phaseDuration, phaseDuration)


@pytest.fixture
def setup_durations(accounts, ftgsale):
    # definition of Sale's Phases durations
    phaseDuration = 86400  # one day
    return ftgsale.setPhasesDurations(phaseDuration, phaseDuration, phaseDuration)


@pytest.fixture
def setup_tiersmin(accounts, ftgsale):
    # definition of Tiers minimum ftg locked staking
    RUBY_MIN = 100_000 * 10 ** 18
    EMERALD_MIN = 250_000 * 10 ** 18
    SAPPHIRE_MIN = 500_000 * 10 ** 18
    DIAMOND_MIN = 1_000_000 * 10 ** 18
    return ftgsale.setTiersMinFTGStakings(
        RUBY_MIN, EMERALD_MIN, SAPPHIRE_MIN, DIAMOND_MIN
    )


@pytest.fixture
def setup_factors(accounts, ftgsale):
    # definition of tiers allocation factors
    return ftgsale.setTiersTokensAllocationFactors(2, 4, 8, {"from": accounts[0]})


def test_registration_phase(
    setup_durations,
    setup_tiersmin,
    setup_factors,
    ftgsale,
    nrt,
    accounts,
    ftgtoken,
    investtoken,
):
    # setup fixtures applied
    # we launch next phase
    ftgsale.launchNextPhase({"from": accounts[0]})
    # verifies that we are in registration phase of the sale
    assert ftgsale.salePhase() == 1
    # stakeholder prepare to participate
    staking1 = 1_100_000
    ftgtoken.approve(ftgstaking, staking1, {"from": accounts[1]})
    ftgstaking.stake(staking1, 2592000, {"from": accounts[1]})

    """ 

    


    ftgsale.launchNextPhase({"from": accounts[0]})

    # register phase
    assert ftgsale.salePhase() == 1

    days30 = 2592000
    stakeAmount = 1_100_000
    ftgtoken.approve(ftgstaking, stakeAmount, {"from": accounts[1]})
    ftgstaking.stake(stakeAmount, days30, {"from": accounts[1]})

    ftgsale.registerForSale({"from": accounts[1]})

    assert ftgsale.participants(accounts[1]) == (0, 0, True, DIAMOND)

    days30 = 2592000
    stakeAmount = 110_000
    ftgtoken.approve(ftgstaking, stakeAmount, {"from": accounts[2]})
    ftgstaking.stake(stakeAmount, days30, {"from": accounts[2]})

    ftgsale.registerForSale({"from": accounts[2]})

    assert ftgsale.participants(accounts[2]) == (0, 0, True, RUBY)

    assert ftgsale.tiersNbOFParticipants(RUBY) == 1
    assert ftgsale.tiersNbOFParticipants(DIAMOND) == 1

    assert ftgsale.checkTierEligibility(accounts[1]) == DIAMOND
    assert ftgsale.checkTierEligibility(accounts[2]) == RUBY

    timeTravel = day1 + 60 * 60
    chain.sleep(timeTravel)

    ftgsale.launchNextPhase({"from": accounts[0]})

    # guaranteed phase
    assert ftgsale.salePhase() == 2

    bamount = 100 * 10 ** 18

    assert investtoken.balanceOf(accounts[1]) == 10_000_000 * 10 ** 18

    investtoken.approve(ftgsale, bamount, {"from": accounts[1]})
    ftgsale.buytoken(bamount, {"from": accounts[1]})

    assert nrt.balanceOf(accounts[1]) == bamount

    # how much can buy?
    assert ftgsale.n() == 1111111111111111111111111111111111

    # TODO test cant buy more than diamond

    # ruby cant buy?
    bamount = 100 * 10 ** 18

    investtoken.approve(ftgsale, bamount, {"from": accounts[2]})
    ftgsale.buytoken(bamount, {"from": accounts[2]}) """

    # investAmount = 10_000
    # buyTokenamount = investAmount/ (_tokenPriceInUSD/10**18)

    # investtoken.approve(ftgsale, investAmount*10, {"from": accounts[2]})
    # assert investtoken.allowance(accounts[2], ftgsale) == investAmount*10
    # #TODO should fail
    # with brownie.reverts():
    #     ftgsale.buytoken(buyTokenamount, {"from": accounts[2]})

    ##### public phase

    """ timeTravel = day1 + 60 * 60
    chain.sleep(timeTravel)

    ftgsale.launchNextPhase({"from": accounts[0]})
    assert ftgsale.salePhase() == 3

    investAmount = 1_000
    buyTokenamount = investAmount / (_tokenPriceInUSD / 10 ** 18)

    assert buyTokenamount == 100_000

    investtoken.approve(ftgsale, investAmount, {"from": accounts[2]})
    assert investtoken.allowance(accounts[2], ftgsale) == investAmount
    ftgsale.buytoken(buyTokenamount, {"from": accounts[2]})

    ##### completed phase

    ftgsale.launchNextPhase({"from": accounts[0]})
    assert ftgsale.salePhase() == 4

    investtoken.approve(ftgsale, investAmount, {"from": accounts[2]})
    with brownie.reverts():
        ftgsale.buytoken(buyTokenamount, {"from": accounts[2]}) """
    # assert investtoken.allowance(accounts[2], ftgsale) == investAmount

    # ftgsale.launchNextPhase({"from": accounts[0]})

    # investtoken.approve(ftgsale, bamount, {"from": accounts[1]})
    # alectr.buytoken(bamount, {"from": accounts[1]})

    # investtoken.approve(ftgsale, bamount, {"from": accounts[2]})
    # ftgsale.buytoken(bamount, {"from": accounts[1]})

    # saletoken = MockFTGToken.deploy(30_000_000 * 10**18, {"from": accounts[0]})
    # saletoken.transfer(accounts[1], 10_000_000 * 10**18, {"from": accounts[0]})
    # saletoken.transfer(accounts[2], 1_000_000 * 10**18, {"from": accounts[0]})
    # assert saletoken.balanceOf(accounts[0]) == 19_000_000 * 10**18
    # assert saletoken.balanceOf(accounts[1]) == 10_000_000 * 10**18
    # assert saletoken.balanceOf(accounts[2]) == 1_000_000 * 10**18

    ############ old

    # ftgsale.registerForSale({"from": accounts[2]})

    # print("accounts[0] = ", accounts[0])

    # saectr.setMins(1000000, 500000, 250000, 100000)
    # ftgsale.setAllocs(40, 30, 20, 10)
    # ftgsale.setParticipants(1000, 500, 100, 50)

    # # assert ftgsale.tiersMin(0) == 1000000
    # print(ftgsale.tiersMin(0))
    # print(type(ftgsale.tiersMin(0)))

    # ftgsale.addWhitelist(accounts[1], {"from": owner})
    # assert ftgsale.participants(accounts[1]) == (0, 0, True)

    # # TODO
    # # uint256 amountLocked = uint(IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(account, 30 days));
    # # calculate init staking fee
    # amountlocked = ftgstaking.checkParticipantLockedStaking(accounts[1], days30)
    # assert amountlocked == stakeAmount * (1 - 0.05)

    # # allocTotal[Tiers.RUBY] / tiersParticipants[Tiers.RUBY]

    # assert stakeAmount > ftgsale.tiersMin(3)
    # assert amountlocked > ftgsale.tiersMin(3)

    # assert ftgsale.tiersTotal(1) / ftgsale.tiersParticipants(1) == 40 / 1000
    # # TODO
    # ae = ftgsale.amountEligible(accounts[1], {"from": accounts[1]})
    # assert ae == 1000 * 0.4 * _totalTokensToSell
    # assert ftgsale.totalTokensToSell() == _totalTokensToSell
    # assert ftgsale.tokensSold() == 0

    # saletoken.transfer(ftgsale, _totalTokensToSell, {"from": accounts[0]})
    # assert investtoken.balanceOf(accounts[1]) >= _totalTokensToSell
    # investtoken.approve(ftgsale, 100, {"from": accounts[1]})
    # ftgsale.participate(100, {"from": accounts[1]})

    # # assert ae == totalTokensSold * 40/1000 /10000
    # assert ftgsale.tokensSold() == 100
    # assert ftgsale.investRaised() == 1

    # # assert ftgsale.participants(accounts[1]).tokensBought == 100
    # # assert ftgsale.participants(accounts[1]).amountInvested == 1

    # assert ftgsale.participants(accounts[1]) == (1, 100)

    # assert ftgsale.amountGuaranteedPool() == 1000000
    # assert ftgsale.amountPublicPool() == 1000000

    # print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    # print("chain in test_FTGToken = ", network.chain)
