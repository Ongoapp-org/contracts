#!/usr/bin/python3
import brownie
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking


def test_ftgStaking(accounts, pm, ftgtoken):
    for i in range(1, 3):
        assert ftgtoken.balanceOf(accounts[i])==10000
    # deploy the contract and test mock chainlink data feed
    print("accounts[0] in test_FTGToken = ", accounts[0])
    print("balance ETH/AVAX accounts[0] in test_FTGToken = ", accounts[0].balance())
    print("chain in test_FTGToken = ", network.chain)
    ftgstaking = deploy_FTGStaking(ftgtoken.address)
    ftgtoken.approve(ftgstaking, 1000, {"from": accounts[0]})
    tx=ftgstaking.stake(1000,0, {"from": accounts[0]})
    print(tx.events)
    timeTravel=3650
    chain.sleep(timeTravel)
    ftgtoken.approve(ftgstaking, 10000, {"from": accounts[0]})
    ftgstaking.stake(10000,0, {"from": accounts[0]})
    flexStakes=ftgstaking.getStakes(accounts[0])
    print("stakeholders[accounts[0]].totalStaked=",flexStakes)
    print("Contracts totalFTGStaked=",ftgstaking.getTotalFTGStaked())
    timeTravel=150
    chain.sleep(timeTravel)
    tx=ftgstaking.depositReward(100)
    print(tx.events)
    timeTravel=180
    chain.sleep(timeTravel)
    ftgtoken.approve(ftgstaking, 4000, {"from": accounts[0]})
    ftgstaking.stake(4000,0, {"from": accounts[0]})
    #print("stakeholders[accounts[0]].totalStaked=",ftgstaking.getStakes(accounts[0])[2].totalStaked)
    #print("Contracts totalFTGStaked=",ftgstaking.totalFTGStaked)
    ftgstaking.depositReward(200)
    timeTravel=100
    chain.sleep(timeTravel)
    ftgstaking.depositReward(300)
    timeTravel=200
    chain.sleep(timeTravel)
    ftgtoken.approve(ftgstaking, 100, {"from": accounts[0]})
    ftgstaking.stake(100,0, {"from": accounts[0]})
    rewardsList=ftgstaking.getRewardsList()
    print("rewardsList=",rewardsList)
    print("stakeholders[accounts[0]].flexStakes=",ftgstaking.getStakes(accounts[0]))
    print("Before Reward update: stakeholders[accounts[0]].totalReward=",ftgstaking.getAccountRewardInfo(accounts[0]))
    tx = ftgstaking.updateReward()
    print(tx.events)
    print("After Reward update: stakeholders[accounts[0]].totalReward=",ftgstaking.getAccountRewardInfo(accounts[0]))
    # in this example, startindex=1, for loop goes from 1 to 3 (3 passes): 
    # i=1, rewardsList[i].rewardPer1BFTG =9132420,  stakeholderStakeIndexAtRewardTime = 1,rewardsList[i].rewardPer1BFTG =10950,->rewardSum=99 (correct)
    # i=2, rewardsList[i].rewardPer1BFTG =13377926,  stakeholderStakeIndexAtRewardTime = 2,rewardsList[i].rewardPer1BFTG =14950,->rewardSum=99+199=298 (correct)
    # i=3, rewardsList[i].rewardPer1BFTG =20066889,  stakeholderStakeIndexAtRewardTime = 2,rewardsList[i].rewardPer1BFTG =14950,->rewardSum=99+199+299=597 (correct)
    # first testing okay, but there may be configurations/cases causing error, need to be checked further and compared gaswise with simpler methods calculating/updating 
    # onchain rewards for every stakeholder every time a reward is deposited.
    # Also is precision set to 9 digits enough? ... and is integer rounding acceptable?

    # test if stakeholder partly unstakes
    tx = ftgstaking.unstake(1000,0, {"from": accounts[0]})
    print(tx.events)
    # test if stakeholder unstakes completely
    tx = ftgstaking.unstake(20000,0, {"from": accounts[0]})
    print(tx.events)
    rewardsList=ftgstaking.getRewardsList()
    print("rewardsList=",rewardsList)
    print("stakeholders[accounts[0]].flexStakes=",ftgstaking.getStakes(accounts[0]))