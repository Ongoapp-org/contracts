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
def ntt(accounts, NTT):
    # accounts[0] deploys NTT contract
    ntt = NTT.deploy("NTT", 18, {"from": accounts[0]})
    return ntt


@pytest.fixture(scope="module", autouse=True)
def ftgsale(accounts, ntt, ftgstaking, ftgtoken, investtoken):
    # FTGSale deployment
    _totalTokensToSell = 10_000_000
    _totalToRaise = 100_000 * 10 ** 18
    # token price (price of 1 token = 10**18 "tokenWei" in investToken)
    _tokenPrice = int(_totalToRaise / _totalTokensToSell)
    print("_tokenPrice = ", _tokenPrice)
    # accounts[0] deploys FTGSale contract
    ftgsale = FTGSale.deploy(
        ntt,
        investtoken,
        ftgstaking,
        _tokenPrice,
        _totalTokensToSell,
        _totalToRaise,
        {"from": accounts[0]},
    )
    # add ownership of ntt to ftgsale
    ntt.addOwner(ftgsale, {"from": accounts[0]})
    return ftgsale


def test_setup_phase(ftgsale, ntt, accounts, ftgtoken, investtoken):
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
    ntt,
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
    ntt,
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
    for i in range(1, 5):
        maxNb = (
            ftgsale.getTiersTokensAllocationFactor(i) * ftgsale.maxNbTokensPerPartRuby()
        )
        print(
            "Tier", i, "max purchaseable tokens per participant in GP:", maxNb,
        )
        assert maxNb == ftgsale.maxNbTokensPerPartRuby() * 2 ** (i - 1)
    # check total number of participants
    ftgsale.NbOfParticipants() == 5
    # participants buy tokens
    print("tokenPrice =", ftgsale.tokenPrice())
    tokenAmount0 = 100_000  # (in token)
    investTokenAmount0 = tokenAmount0 * ftgsale.tokenPrice()  # in investToken
    print("investTokenAmount0 =", investTokenAmount0, "investTokenWei")
    investtoken.approve(ftgsale, investTokenAmount0, {"from": accounts[0]})
    tx = ftgsale.buytoken(tokenAmount0, {"from": accounts[0]})
    print(tx.events)
    tokenAmount2 = 400_000  # (in token)
    investTokenAmount2 = tokenAmount2 * ftgsale.tokenPrice()  # in investToken
    print("investTokenAmount2 =", investTokenAmount2, "investTokenWei")
    investtoken.approve(ftgsale, investTokenAmount2, {"from": accounts[2]})
    ftgsale.buytoken(tokenAmount2, {"from": accounts[2]})
    # verify balances
    assert ftgsale.tokensSold() == tokenAmount0 + tokenAmount2
    assert ftgsale.investmentRaised() == investTokenAmount0 + investTokenAmount2
    print(
        "ftgsale.getParticipantInfo(accounts[0]) =",
        ftgsale.getParticipantInfo(accounts[0]),
    )
    print(
        "ftgsale.getParticipantInfo(accounts[2]) =",
        ftgsale.getParticipantInfo(accounts[2]),
    )
    assert ftgsale.getParticipantInfo(accounts[0])[0] == tokenAmount0
    assert ftgsale.getParticipantInfo(accounts[2])[0] == tokenAmount2
    assert ntt.balanceOf(accounts[0]) == tokenAmount0
    assert ntt.balanceOf(accounts[2]) == tokenAmount2
    # verify cannot buy more than entitled
    # accounts[4] is SAPPHIRE TIER, he cannot purchase more than 1_250_000 tokens
    tokenAmount4 = 1_300_000  # (in token)
    investTokenAmount4 = tokenAmount4 * ftgsale.tokenPrice()  # in investToken
    print("investTokenAmount4 =", investTokenAmount4, "investTokenWei")
    investtoken.approve(ftgsale, investTokenAmount4, {"from": accounts[4]})
    with brownie.reverts("Maximum allowed number of tokens exceeded"):
        ftgsale.buytoken(tokenAmount4, {"from": accounts[4]})
    # verify cannot buy when pool ended
    # time travel to end guaranteed pool phase
    chain.sleep(ftgsale.guaranteedPoolPhaseDuration() + 60)
    tokenAmount4 = 1_000_000  # (in token)
    investTokenAmount4 = tokenAmount4 * ftgsale.tokenPrice()  # in investToken
    print("second trial investTokenAmount4 =", investTokenAmount4, "investTokenWei")
    investtoken.approve(ftgsale, investTokenAmount4, {"from": accounts[4]})
    with brownie.reverts("Guaranteed Pool Phase ended"):
        ftgsale.buytoken(tokenAmount4, {"from": accounts[4]})

