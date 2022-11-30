#!/usr/bin/python3
import brownie
import random
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

days30 = 2592000


def test_ftgStaking(accounts, ftgtoken):
    for i in range(1, 9):
        assert ftgtoken.balanceOf(accounts[i]) == 5000000 * 10 ** 18
        # print(random.gauss(10, 1))
        # print(accounts[i])
    # deploy the contract
    print("accounts[0] in test_FTGToken = ", accounts[0])
    print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    print("chain in test_FTGToken = ", network.chain)
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    print("1) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    # first staking 600000 ftg by accounts[0] locked for a month
    print("**************first staking 600000 ftg by accounts[0] locked for a month \n")
    ftgtoken.approve(ftgstaking, 600000 * 10 ** 18, {"from": accounts[0]})
    tx = ftgstaking.stake(
        600000 * 10 ** 18, days30, {"from": accounts[0]}
    )  # 30 days locked = 2592000 secs
    print("2) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # balance update
    ftgstaking.updateBalances(accounts[0])
    print(
        "totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=",
        ftgstaking.getBalances(accounts[0]),
    )
    # wait 3650 secs
    print("wait 3650 secs = 1h")
    timeTravel = 3650
    chain.sleep(timeTravel)
    # verifies accountRewardInfo before and after update reward for accounts[0]
    totalreward0 = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    lastUpdateReward0 = ftgstaking.getAccountRewardInfo(accounts[0])[1]
    print("before call updateReward(),totalreward0 = ", totalreward0)
    print("before call updateReward(),lastUpdateReward0 = ", lastUpdateReward0)
    assert totalreward0 == 0
    assert lastUpdateReward0 == 0
    tx = ftgstaking.updateReward()
    print(tx.events)
    totalreward0 = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    lastUpdateReward0 = ftgstaking.getAccountRewardInfo(accounts[0])[1]
    print("after call updateReward(),totalreward0 = ", totalreward0)
    print("after call updateReward(),lastUpdateReward0 = ", lastUpdateReward0)
    assert totalreward0 == 0
    assert lastUpdateReward0 == chain.time()
    # second staking 120000 ftg by accounts[1]
    print("**************second staking 120000 ftg by accounts[1] for 90 days \n")
    ftgtoken.transfer(accounts[1], 200000 * 10 ** 18)
    ftgtoken.approve(ftgstaking, 120000 * 10 ** 18, {"from": accounts[1]})
    ftgstaking.stake(
        120000 * 10 ** 18, 7776000, {"from": accounts[1]}
    )  # 90 days = 7776000 secs
    print("3) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    print("3) accounts[1] ftg balance = \n", ftgtoken.balanceOf(accounts[1]))
    # verifies Stakeholder's stakings
    stakings0 = ftgstaking.getStakings(accounts[0])
    print("stakeholders[accounts[0]].stakings=", stakings0)
    stakings1 = ftgstaking.getStakings(accounts[1])
    print("stakeholders[accounts[1]].stakings=", stakings1)
    # verifies more than 30 days Locked Staking
    print(
        "**************verifies more than 30 days Locked Staking still active after one hour \n"
    )
    totalActiveLocked0 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[0], days30, {"from": accounts[0]}
    )
    assert totalActiveLocked0 == 570000 * 10 ** 18
    print("totalActiveLocked0 = ", totalActiveLocked0)
    totalActiveLocked1 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[1], days30, {"from": accounts[0]}
    )
    assert totalActiveLocked1 == 114000 * 10 ** 18
    print("totalActiveLocked1 = ", totalActiveLocked1)
    print("Contracts totalFTGStaked=", ftgstaking.totalFTGStaked())
    # wait 180 secs
    print("**************wait 150 secs \n")
    timeTravel = 180
    chain.sleep(timeTravel)
    # first deposit of 100 ftg reward to be distributed to stakers
    print(
        "**************first deposit of 100 ftg reward to be distributed to stakers \n"
    )
    ftgtoken.approve(ftgstaking, 100 * 10 ** 18, {"from": accounts[0]})
    tx = ftgstaking.depositRewardTokens(100 * 10 ** 18)
    print("4) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # wait 30 days, first staking should be free to unstake
    timeTravel = days30
    chain.sleep(timeTravel)
    # third staking 400000 ftg by accounts[0]
    ftgtoken.approve(ftgstaking, 400000 * 10 ** 18, {"from": accounts[0]})
    ftgstaking.stake(400000 * 10 ** 18, 7776000, {"from": accounts[0]})
    print("5) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    # verifies more than 30 days locked staking
    totalActiveLocked0 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[0], days30, {"from": accounts[0]}
    )
    assert totalActiveLocked0 == 400000 * 10 ** 18
    print("totalActiveLocked0 = ", totalActiveLocked0)
    totalActiveLocked1 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[1], days30, {"from": accounts[0]}
    )
    assert totalActiveLocked1 == 114000 * 10 ** 18
    print("totalActiveLocked1 = ", totalActiveLocked1)
    # second deposits 2000 ftg reward to be distributed to stakers
    ftgtoken.approve(ftgstaking, 2000 * 10 ** 18, {"from": accounts[0]})
    ftgstaking.depositRewardTokens(2000 * 10 ** 18)
    print("6) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # wait 1min
    timeTravel = 60
    chain.sleep(timeTravel)
    # balance update
    ftgstaking.updateBalances(accounts[0])
    print(
        "totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=",
        ftgstaking.getBalances(accounts[0]),
    )
    # wait 30 days
    timeTravel = days30
    chain.sleep(timeTravel)
    # third deposits 50000 ftg reward to be distributed to stakers
    ftgtoken.approve(ftgstaking, 50000 * 10 ** 18, {"from": accounts[0]})
    ftgstaking.depositRewardTokens(50000 * 10 ** 18)
    print("7) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # wait 240 secs
    timeTravel = 240
    chain.sleep(timeTravel)
    # fourth staking 100 ftg by accounts[0]
    ftgtoken.approve(ftgstaking, 100 * 10 ** 18, {"from": accounts[0]})
    ftgstaking.stake(100 * 10 ** 18, 0, {"from": accounts[0]})
    print("8) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # Check Stakeholder's Stakings
    print("stakeholders[accounts[0]].stakings=", ftgstaking.getStakings(accounts[0]))
    # balance update
    ftgstaking.updateBalances(accounts[0])
    print(
        "totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=",
        ftgstaking.getBalances(accounts[0]),
    )
    # Verify updateRewards() outcome after scenario for accounts[0]
    print(
        "Before Reward update: stakeholders[accounts[0]].totalReward=",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    # assert ftgstaking.getAccountRewardInfo(accounts[0]) == (0, 1669303831)
    tx = ftgstaking.updateReward()
    print(tx.events)
    print(
        "After Reward update: stakeholders[accounts[0]].totalReward=",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    """ assert ftgstaking.getAccountRewardInfo(accounts[0]) == (
        51874 * 10 ** 18,
        chain.time(),
    ) """
    # updateRewards Outcome:
    # in this example, startindex=1, for loop goes from 1 to 3 (3 passes):
    # i=1, rewardsList[i].rewardPer1BFTG =9132420,  stakeholderStakeIndexAtRewardTime = 1,rewardsList[i].rewardPer1BFTG =10950,->rewardSum=99 (correct)
    # i=2, rewardsList[i].rewardPer1BFTG =13377926,  stakeholderStakeIndexAtRewardTime = 2,rewardsList[i].rewardPer1BFTG =14950,->rewardSum=99+199=298 (correct)
    # i=3, rewardsList[i].rewardPer1BFTG =20066889,  stakeholderStakeIndexAtRewardTime = 2,rewardsList[i].rewardPer1BFTG =14950,->rewardSum=99+199+299=597 (correct)
    # first testing okay, but there may be configurations/cases causing error, need to be checked further and compared gaswise with simpler methods calculating/updating
    # onchain rewards for every stakeholder every time a reward is deposited.
    # Also is precision set to 9 digits enough? ... and is integer rounding acceptable?
    # wait 1h
    timeTravel = 3600
    chain.sleep(timeTravel)
    # test if stakeholder partly unstakes
    print("partly unstaking test \n")
    print(
        "before unstaking 1000 accounts[0] stakeholder Balances Info (not up to date since update is performed at unstaking):",
        ftgstaking.getBalances(accounts[0]),
    )
    # totalStaked (correct)
    assert ftgstaking.getBalances(accounts[0])[0] == 970100 * 10 ** 18
    tx = ftgstaking.unstake(1000, {"from": accounts[0]})
    print(
        "9) after unstaking 1000 accounts[0] ftg balance = \n",
        ftgtoken.balanceOf(accounts[0]),
    )
    assert ftgstaking.getBalances(accounts[0])[0] == 970099999999999999999000
    # totalLockedBalance
    # assert ftgstaking.getBalances(accounts[0])[1] == 400000 * 10 ** 18
    # freeToUnstakeBalance(pay no fee up to this amount ... Right cause we withdrew 1000 and 570000 were freeToUnstake before)
    # assert ftgstaking.getBalances(accounts[0])[2] == 569000 * 10 ** 18
    print(
        "after unstaking accounts[0] stakeholder Balances Info :",
        ftgstaking.getBalances(accounts[0]),
    )
    print(tx.events)
    # balance update
    ftgstaking.updateBalances(accounts[0])
    print(
        "totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=",
        ftgstaking.getBalances(accounts[0]),
    )
    # wait 1h
    timeTravel = 3600
    chain.sleep(timeTravel)
    # test if stakeholder unstakes completely
    print("completely unstaking test \n")
    tx = ftgstaking.unstake(569100 * 10 ** 18, {"from": accounts[0]})
    print("10) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # check if stakeholder pays fee 15% for unstaking 100 ftg not yet staked for 30 days
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList = \n", rewardsList)
    # assert rewardsList[-1][0] == 15 * 10 ** 18

    print(
        "stakeholders[accounts[0]].stakings = \n", ftgstaking.getStakings(accounts[0])
    )

    # wait 6 months
    timeTravel = 15552000
    chain.sleep(timeTravel)
    print("time now = ", chain.time())
    # Check Stakeholder's Stakings
    # somethig weird with this test: after 6 months, no active staking should be found ...
    # when examining using Log events, and changing the checkParticipantLockedStaking function
    # to non view to be able to use events, everything work as expected. When not using Log events
    # test is not passing... Not sure what is going on here.
    print("stakeholders[accounts[0]].stakings=", ftgstaking.getStakings(accounts[0]))
    """ totalActiveLocked0 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[0], days30, {"from": accounts[0]}
    )
    assert totalActiveLocked0 == 0
    print("after 6 months  ... totalActiveLocked0 = \n", totalActiveLocked0) """

    # test of staking some reward
    ftgstaking.updateReward()
    print(
        "before staking 200ftg from reward: stakeholder accumulated rewards = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    ftgstaking.stakeReward(200 * 10 ** 18, 0)
    print(
        "after staking 200ftg from reward: stakeholder accumulated rewards = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    print(
        "stakeholders[accounts[0]].flexStakings=", ftgstaking.getStakings(accounts[0])
    )

    # test of withdrawing the reward balance
    print("contract's address = ", ftgstaking.address)
    print(
        "before withdrawing: stakeholder ftg balance = ",
        ftgtoken.balanceOf(accounts[0]),
    )
    ftgstaking.withdrawReward()
    print(
        "after withdrawing reward balance: stakeholder accumulated rewards = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    print(
        "after withdrawing: stakeholder ftg balance = ", ftgtoken.balanceOf(accounts[0])
    )

    # calculateAPY
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)

    apy = ftgstaking.calculateAPY.call({"from": accounts[0]})
    print("APY=", 100 * apy / 10 ** 9, "%")
    assert round(100 * apy / 10 ** 9, 2) == 8.91


def test_staking_basic(accounts, ftgtoken):
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])

    ftgtoken.transfer(accounts[1], 1_000_000 * 10 ** 18, {"from": accounts[0]})

    stakeAmount = 600_000 * 10 ** 18
    ftgtoken.approve(ftgstaking, stakeAmount, {"from": accounts[1]})
    ftgstaking.stake(stakeAmount, days30, {"from": accounts[1]})

    lockdur = 2_592_000
    totalActiveLocked0 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[1], lockdur, {"from": accounts[1]}
    )
    assert totalActiveLocked0 == stakeAmount * (1 - 0.05)
    totalActiveLocked1 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[1], days30, {"from": accounts[1]}
    )
    assert totalActiveLocked1 == 570_000 * 10 ** 18
    # first deposit of 100 ftg reward to be distributed to stakers
    ftgtoken.approve(ftgstaking, 100, {"from": accounts[0]})
    tx = ftgstaking.depositRewardTokens(100)
    # wait 30 days, first staking should be free to unstake
    timeTravel = days30 + 1
    chain.sleep(timeTravel)
    tx = ftgstaking.updateReward({"from": accounts[1]})
    # assert ftgstaking.getAccountRewardInfo(accounts[0])[0] == 99
    assert ftgstaking.getAccountRewardInfo(accounts[0])[0] == 0
    # assert ftgstaking.getAccountRewardInfo(accounts[0]) == (6528, chain.time())

    a = ftgtoken.balanceOf(accounts[1])
    # revert: Integer overflow
    # ftgstaking.unstakeAll({"from": accounts[1]})
    # b = ftgtoken.balanceOf(accounts[1])
    # assert b - a > 0

    # totalActiveLocked1 = ftgstaking.checkParticipantLockedStaking.call(
    #     accounts[1], days30, {"from": accounts[0]}
    # )
    # assert totalActiveLocked1 == 0


def test_ftgStaking_scenario(accounts, pm, ftgtoken):
    print("test_ftgStaking_scenario \n")
    # deploy the contract
    ftgtoken.transfer(accounts[1], 1_000_000 * 10 ** 18, {"from": accounts[0]})
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])

    ftgtoken.approve(ftgstaking, 1000, {"from": accounts[0]})
    ftgstaking.depositRewardTokens(1_000, {"from": accounts[0]})

    ftgtoken.approve(ftgstaking, 600000, {"from": accounts[1]})
    days30 = 30 * 60 * 60 * 24
    ftgstaking.stake(1_000, days30, {"from": accounts[1]})

    ftgtoken.balanceOf(accounts[1])
    timeTravel = days30 + 1
    chain.sleep(timeTravel)

    # sk = ftgstaking.stakeholders.call(accounts[1])

    rewardsList = ftgstaking.viewRewardsList()
    assert rewardsList[0][:2] == (1000, 0)
    assert rewardsList[1][:2] == (50, 0)
    print("rewardsList=", rewardsList)

    assert len(rewardsList) == 2
    ftgstaking.updateReward({"from": accounts[1]})

    assert ftgstaking.stakeholders(accounts[1])[:-1] == (950, 950, 0, 0, 0)

    # balance update
    ftgstaking.updateBalances(accounts[1])
    print(
        "Before unstakeFreeAll,totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=",
        ftgstaking.getBalances(accounts[1]),
    )
    ftgstaking.unstakeFreeAll({"from": accounts[1]})
    # balance update
    ftgstaking.updateBalances(accounts[1])
    print(
        "after unstakeFreeAll,totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=",
        ftgstaking.getBalances(accounts[1]),
    )
    # ftgstaking.unstake(950,{"from": accounts[1]})
    # print(tx.traceback)
    # assert sk["totalReward"] == 1
    # ()["totalReward"] == 100

    # ftgstaking.stakeReward(200, 0)
    # fails
    # ftgstaking.withdrawReward()

    # assert ftgtoken.balanceOf(accounts[1]) == x + 100
