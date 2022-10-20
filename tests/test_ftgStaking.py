#!/usr/bin/python3
import brownie
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking


def test_ftgStaking(accounts, pm, ftgtoken):
    for i in range(1, 3):
        assert ftgtoken.balanceOf(accounts[i]) == 10000
    # deploy the contract
    print("accounts[0] in test_FTGToken = ", accounts[0])
    print("balance accounts[0] in test_FTGToken = ", accounts[0].balance())
    print("chain in test_FTGToken = ", network.chain)
    ftgstaking = deploy_FTGStaking(ftgtoken.address)
    print("1) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    # first staking 1000 ftg by accounts[0]
    ftgtoken.approve(ftgstaking, 1000, {"from": accounts[0]})
    tx = ftgstaking.stake(1000, 0, {"from": accounts[0]})
    print("2) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # wait 3650 secs
    timeTravel = 3650
    chain.sleep(timeTravel)
    # second staking 10000 ftg by accounts[0]
    ftgtoken.approve(ftgstaking, 10000, {"from": accounts[0]})
    ftgstaking.stake(10000, 0, {"from": accounts[0]})
    print("3) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    # verifies Stakeholder's stakings
    flexStakings = ftgstaking.getStakings(accounts[0])
    print("stakeholders[accounts[0]].totalStaked=", flexStakings)
    print("Contracts totalFTGStaked=", ftgstaking.totalFTGStaked())
    # wait 150 secs
    timeTravel = 150
    chain.sleep(timeTravel)
    # first deposit of 100 ftg reward to be distributed to stakers
    ftgtoken.approve(ftgstaking, 100, {"from": accounts[0]})
    tx = ftgstaking.depositReward(100)
    print("4) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # wait 180 secs
    timeTravel = 180
    chain.sleep(timeTravel)
    # third staking 4000 ftg by accounts[0]
    ftgtoken.approve(ftgstaking, 4000, {"from": accounts[0]})
    ftgstaking.stake(4000, 0, {"from": accounts[0]})
    print("5) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    # second deposits 200 ftg reward to be distributed to stakers
    ftgtoken.approve(ftgstaking, 200, {"from": accounts[0]})
    ftgstaking.depositReward(200)
    print("6) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    # wait 100 secs
    timeTravel = 100
    chain.sleep(timeTravel)
    # third deposits 300 ftg reward to be distributed to stakers
    ftgtoken.approve(ftgstaking, 300, {"from": accounts[0]})
    ftgstaking.depositReward(300)
    print("7) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    # wait 200 secs
    timeTravel = 200
    chain.sleep(timeTravel)
    # fourth staking 100 ftg by accounts[0]
    ftgtoken.approve(ftgstaking, 100, {"from": accounts[0]})
    ftgstaking.stake(100, 0, {"from": accounts[0]})
    print("8) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    # Check rewardsList 
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # Check Stakeholder's Stakings
    print("stakeholders[accounts[0]].flexStakings=", ftgstaking.getStakings(accounts[0]))
    # Verify updateRewards() outcome after scenario
    print(
        "Before Reward update: stakeholders[accounts[0]].totalReward=",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    tx = ftgstaking.updateReward()
    print(tx.events)
    print(
        "After Reward update: stakeholders[accounts[0]].totalReward=",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    # updateRewards Outcome:
    # in this example, startindex=1, for loop goes from 1 to 3 (3 passes):
    # i=1, rewardsList[i].rewardPer1BFTG =9132420,  stakeholderStakeIndexAtRewardTime = 1,rewardsList[i].rewardPer1BFTG =10950,->rewardSum=99 (correct)
    # i=2, rewardsList[i].rewardPer1BFTG =13377926,  stakeholderStakeIndexAtRewardTime = 2,rewardsList[i].rewardPer1BFTG =14950,->rewardSum=99+199=298 (correct)
    # i=3, rewardsList[i].rewardPer1BFTG =20066889,  stakeholderStakeIndexAtRewardTime = 2,rewardsList[i].rewardPer1BFTG =14950,->rewardSum=99+199+299=597 (correct)
    # first testing okay, but there may be configurations/cases causing error, need to be checked further and compared gaswise with simpler methods calculating/updating
    # onchain rewards for every stakeholder every time a reward is deposited.
    # Also is precision set to 9 digits enough? ... and is integer rounding acceptable?

    # test if stakeholder partly unstakes
    print("partly unstaking test \n")
    tx = ftgstaking.unstake(1000, 0, {"from": accounts[0]})
    print("9) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # test if stakeholder unstakes completely
    print("completely unstaking test \n")
    tx = ftgstaking.unstake(20000, 0, {"from": accounts[0]})
    print("10) accounts[0] ftg balance = \n",ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList = \n", rewardsList)
    print("stakeholders[accounts[0]].flexStakings = \n", ftgstaking.getStakings(accounts[0]))

    # test of staking some reward
    ftgstaking.updateReward()
    print(
        "before staking 200ftg from reward: stakeholder accumulated rewards = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    ftgstaking.stakeReward(200)
    print(
        "after staking 200ftg from reward: stakeholder accumulated rewards = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    print("stakeholders[accounts[0]].flexStakings=", ftgstaking.getStakings(accounts[0]))

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
