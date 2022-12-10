#!/usr/bin/python3
import pytest
import brownie
from brownie import chain, network, FTGSale, accounts
from scripts.deploy_FTGStaking import deploy_FTGStaking


@pytest.fixture(scope="module", autouse=True)
def ftgstaking(accounts, ftgtoken):
    # ftgstaking deployment
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    return ftgstaking


@pytest.fixture(scope="module", autouse=True)
def nrt(accounts, NRT):
    # accounts[0] deploys NRT contract
    nrt = NRT.deploy("NRT", 18, {"from": accounts[0]})
    return nrt


@pytest.fixture(scope="module", autouse=True)
def ftgsale(accounts, nrt, ftgstaking, ftgtoken, investtoken):
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
    print("********************Setup Phase Tests********************")
    # verifies that we are in setup phase of the sale
    assert ftgsale.salePhase() == 0
    # Tiers enum codes
    NONE = 0
    RUBY = 1
    SAPPHIRE = 2
    EMERALD = 3
    DIAMOND = 4

    # definition of Sale's Phases durations
    phaseDuration = 86400  # one day
    ftgsale.setPhasesDurations(phaseDuration, phaseDuration, phaseDuration)
    assert ftgsale.registrationPhaseDuration() == phaseDuration
    # definition of Tiers minimum ftg locked staking
    RUBY_MIN = 100_000 * 10 ** 18
    SAPPHIRE_MIN = 250_000 * 10 ** 18
    EMERALD_MIN = 500_000 * 10 ** 18
    DIAMOND_MIN = 1_000_000 * 10 ** 18
    ftgsale.setTiersMinFTGStakings(RUBY_MIN, SAPPHIRE_MIN, EMERALD_MIN, DIAMOND_MIN)
    assert ftgsale.tiersMinFTGStaking(NONE) == 0
    assert ftgsale.tiersMinFTGStaking(RUBY) == 100_000 * 10 ** 18
    assert ftgsale.tiersMinFTGStaking(SAPPHIRE) == 250_000 * 10 ** 18
    assert ftgsale.tiersMinFTGStaking(EMERALD) == 500_000 * 10 ** 18
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
    SAPPHIRE_MIN = 250_000 * 10 ** 18
    EMERALD_MIN = 500_000 * 10 ** 18
    DIAMOND_MIN = 1_000_000 * 10 ** 18
    return ftgsale.setTiersMinFTGStakings(
        RUBY_MIN, SAPPHIRE_MIN, EMERALD_MIN, DIAMOND_MIN
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
    ftgstaking,
    nrt,
    accounts,
    ftgtoken,
    investtoken,
):
    print("********************Registration Phase Tests********************")
    # setup fixtures applied
    # Tiers enum codes
    NONE = 0
    RUBY = 1
    SAPPHIRE = 2
    EMERALD = 3
    DIAMOND = 4
    # we launch next phase
    ftgsale.launchNextPhase({"from": accounts[0]})
    # verifies that we are in registration phase of the sale
    assert ftgsale.salePhase() == 1
    # stakeholders prepare to participate
    # BEWARE OF 5% FEES APPLYING ON STAKINGS!
    # staking must  be > tier_min_target/0.95
    # for Ruby, min staking > 105_264 ftg
    # for Sapphire, min staking > 263_158 ftg
    # for Emerald, min staking > 526_316 ftg
    # for Diamond, min staking > 1_052_631 ftg
    staking0 = 530_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking0, {"from": accounts[0]})
    ftgstaking.stake(staking0, 5184000, {"from": accounts[0]})
    staking1 = 1_100_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking1, {"from": accounts[1]})
    ftgstaking.stake(staking1, 2592000, {"from": accounts[1]})
    staking2 = 110_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking2, {"from": accounts[2]})
    ftgstaking.stake(staking2, 3000000, {"from": accounts[2]})
    staking3 = 60_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking3, {"from": accounts[3]})
    ftgstaking.stake(staking3, 6000000, {"from": accounts[3]})
    staking4 = 265_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking4, {"from": accounts[4]})
    ftgstaking.stake(staking4, 2592000, {"from": accounts[4]})
    # registration
    ftgsale.registerForSale({"from": accounts[0]})
    tx = ftgsale.registerForSale({"from": accounts[1]})
    print(tx.events)
    ftgsale.registerForSale({"from": accounts[2]})
    # verification of their registration
    print(
        "checkParticipantLockedStaking(accounts[0], 2592000)=",
        ftgstaking.checkParticipantLockedStaking(accounts[0], 2592000).return_value,
    )
    assert ftgsale.participants(accounts[0]) == (0, 0, True, EMERALD)
    assert ftgsale.participants(accounts[1]) == (0, 0, True, DIAMOND)
    assert ftgsale.participants(accounts[2]) == (0, 0, True, RUBY)
    # verification that the nb of participants per Tier was correctly incremented
    assert ftgsale.tiersNbOFParticipants(RUBY) == 1
    assert ftgsale.tiersNbOFParticipants(DIAMOND) == 1
    # verifies that a participant cannot register a second time
    with brownie.reverts("already registered"):
        ftgsale.registerForSale({"from": accounts[2]})
    # verifies that a participant of NONE Tier cannot register
    with brownie.reverts("Not enough locked Staking"):
        ftgsale.registerForSale({"from": accounts[3]})
    # time travel 86500 secs = 1 day and 100 secs
    timeTravel = 86500
    chain.sleep(timeTravel)
    # registration should be over
    # any registration attempts should be reverted
    with brownie.reverts("Registration Phase ended"):
        ftgsale.registerForSale({"from": accounts[4]})


def participants_stakings(ftgtoken, ftgstaking):
    staking0 = 530_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking0, {"from": accounts[0]})
    ftgstaking.stake(staking0, 5184000, {"from": accounts[0]})
    staking1 = 1_100_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking1, {"from": accounts[1]})
    ftgstaking.stake(staking1, 2592000, {"from": accounts[1]})
    staking2 = 110_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking2, {"from": accounts[2]})
    ftgstaking.stake(staking2, 3000000, {"from": accounts[2]})
    staking3 = 160_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking3, {"from": accounts[3]})
    ftgstaking.stake(staking3, 6000000, {"from": accounts[3]})
    staking4 = 265_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, staking4, {"from": accounts[4]})
    ftgstaking.stake(staking4, 2592000, {"from": accounts[4]})


@pytest.fixture
def participants_preparation(ftgtoken, ftgstaking):
    # participants prepare for sale participation
    return participants_stakings(ftgtoken, ftgstaking)


""" @pytest.fixture
def launch_registration(ftgsale):
    return ftgsale.launchNextPhase({"from": accounts[0]}) """


def registration(ftgsale):
    # admin launch registration phase
    ftgsale.launchNextPhase({"from": accounts[0]})
    # participants register
    for i in range(5):
        ftgsale.registerForSale({"from": accounts[i]})


@pytest.fixture
def registration_phase(ftgsale):
    # admin launch registration and participants register
    return registration(ftgsale)


def test_guaranteed_phase(
    setup_durations,
    setup_tiersmin,
    setup_factors,
    participants_preparation,
    registration_phase,
    ftgsale,
    ftgstaking,
    nrt,
    accounts,
    ftgtoken,
    investtoken,
):
    print("********************Guaranteed Phase Tests********************")
    # Tiers enum codes
    NONE = 0
    RUBY = 1
    SAPPHIRE = 2
    EMERALD = 3
    DIAMOND = 4
    # setup fixtures applied...
    # registration fixtures applied...:
    # verif accounts[0] staking for instance:
    assert (
        ftgstaking.getStakings(accounts[0])[-1][0]
        == 530000 * 10 ** 18 - ftgstaking.STAKING_FEE() * 530000 * 10 ** 18 / 100
    )
    # verif accounts[4] registration for instance
    assert ftgsale.participants(accounts[4]) == (0, 0, True, SAPPHIRE)
    # time travel to end registration phase
    chain.sleep(ftgsale.registrationPhaseDuration() + 60)
    # admin launch guaranteed phase
    ftgsale.launchNextPhase({"from": accounts[0]})
    # verif that we are in guaranteed phase of the sale
    assert ftgsale.salePhase() == 2
    # check maxNbTokensPerPartRuby calculation
    print("ftgsale.maxNbTokensPerPartRuby =", ftgsale.maxNbTokensPerPartRuby())
    sumFNP = 0
    expectedNbParticipants = [0, 2, 1, 1, 1]
    for i in range(1, 5):
        # check nb of participants per Tier
        print(
            "Tiers ", i, ": nb of  participants =", ftgsale.getTiersNbOFParticipants(i)
        )
        assert ftgsale.getTiersNbOFParticipants(i) == expectedNbParticipants[i]
        # calculate sumFNP
        sumFNP += ftgsale.getTiersTokensAllocationFactor(
            i
        ) * ftgsale.getTiersNbOFParticipants(i)
    assert ftgsale.maxNbTokensPerPartRuby() == int(ftgsale.totalTokensToSell() / sumFNP)
    # check total number of participants
    ftgsale.NbOfParticipants() == 5

    """ 

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
