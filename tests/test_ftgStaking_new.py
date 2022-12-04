import brownie
import random, math
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

# We want to perform more systematic tests using many stakers taking random actions
def test_ftgStaking_new_general(accounts, ftgtoken):
    print("\n")
    print("++++++++++++++++test_ftgStaking_fixedAPY+++++++++++++++++ \n")
    print("\n")
    # initial ftg balances
    assert ftgtoken.balanceOf(accounts[0]) == 155000000 * 10 ** 18
    for i in range(1, 50):
        assert ftgtoken.balanceOf(accounts[i]) == 5000000 * 10 ** 18
    # deploy the contract
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    # approvals
    ftgtoken.approve(ftgstaking, 150000000 * 10 ** 18, {"from": accounts[0]})
    for i in range(1, 50):
        # approve contract to transfer ftg for accounts[i]
        ftgtoken.approve(ftgstaking, 5000000 * 10 ** 18, {"from": accounts[i]})
    # first staking accounts[0]
    print("**************first staking 600000 ftg by accounts[0] locked for a month \n")
    print("1) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    tx = ftgstaking.stake(
        600000 * 10 ** 18, 2592000, {"from": accounts[0]}
    )  # 30 days locked = 2592000 secs
    print("2) accounts[0] ftg balance = \n", ftgtoken.balanceOf(accounts[0]))
    print(tx.events)
    # balance update
    ftgstaking.updateBalances(accounts[0])
    bal0 = ftgstaking.getBalances(accounts[0])
    print("totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=", bal0)
    # wait 3600 secs
    print("wait 3600 secs = 1h")
    timeTravel0 = 3600
    chain.sleep(timeTravel0)
    # accounts[0] did his first staking one hour ago
    # stakeholder's reward balance has not been updated yet
    print(
        "before calling updateReward(),rewardInfo = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    assert ftgstaking.getAccountRewardInfo(accounts[0]) == (0, 0)
    # updateReward
    print("update reward!")
    tx = ftgstaking.updateReward({"from": accounts[0]})
    print(tx.events)
    # verifies reward calculation after update
    print("accounts[0]'s stakings = ", ftgstaking.getStakings(accounts[0]))
    assert bal0[0] == ftgstaking.getStakings(accounts[0])[-1][0]
    print(
        "after calling updateReward(),rewardInfo = ",
        ftgstaking.getAccountRewardInfo(accounts[0]),
    )
    print("staking timestamp", ftgstaking.getStakings(accounts[0])[-1][1])
    timeElapsed = chain.time() - ftgstaking.getStakings(accounts[0])[-1][1]
    print("timeElapsed", timeElapsed)
    assert timeTravel0 == timeElapsed
    rewardRatePer1TFTG = ftgstaking.rewardRatePer1TFTG()
    print("rewardRatePer1TFTG = ", rewardRatePer1TFTG)
    print("staking = ", bal0[0], "ftg")
    rewardCalc = int(timeTravel0 * bal0[0] * rewardRatePer1TFTG / 10 ** 12)
    print("reward calculation = ", rewardCalc)
    assert ftgstaking.getAccountRewardInfo(accounts[0]) == (rewardCalc, chain.time())
