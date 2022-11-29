import brownie
import random, math
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

# We want to perform more systematic tests using many stakers taking random actions
def test_ftgStaking_manyStakers(accounts, ftgtoken):
    print("\n")
    print("++++++++++++++++test_ftgStaking_manyStakers+++++++++++++++++ \n")
    print("\n")
    # initial ftg balances
    assert ftgtoken.balanceOf(accounts[0]) == 210000000 * 10 ** 18
    for i in range(1, 10):
        assert ftgtoken.balanceOf(accounts[i]) == 10000000 * 10 ** 18
    # deploy the contract
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    # approvals
    ftgtoken.approve(ftgstaking, 210000000 * 10 ** 18, {"from": accounts[0]})
    print("accounts[0] allowance=", ftgtoken.allowance(accounts[0], ftgstaking))
    for i in range(1, 10):
        # approve contract to transfer ftg for accounts[i]
        ftgtoken.approve(ftgstaking, 10000000 * 10 ** 18, {"from": accounts[i]})
    # Scenario of events at random times (time laps between events
    #  normally distributed around some mean time laps). Probability of events
    # is decreasing with increasing label number of the event type.
    #  Most probable event is a random stakeholder stakes random amounts (exponentialy distributed,
    #  higher proba for lower staking amounts), lockduration randomly chosen depending on staking amount
    # (it makes more sense to lock larger amount for longer time (?)). Secondly most probable event is
    #  unstakingFreeAll when a random stakeholder unstake its staking without incuring any fee.
    # Thirdly most probable events are just a reward updates, mostly for testing the rewardUpdate()
    # method since it is the most delicate part of the contract for accurate reward calculation.
    # Next most probable event is reward deposit from the admin for fixed amount of 1 M ftg.
    # Next most probable eventis the reward withdrawal by a random stakeholder. Then less probable events
    # of unstaking all ftg by a random stakeholder possibly incuring fee. Lastly, most unlikely events
    # are the staking of rewards by a random stakeholder.
    lastDepositTime = chain.time()
    for i in range(30):
        # reward deposit of 1M ftg every week
        if chain.time() - lastDepositTime > 7 * 86400:
            print("1M Reward Deposit!")
            ftgstaking.depositRewardTokens(1000000 * 10 ** 18)
            lastDepositTime = chain.time()
        # 0:staking,1:unstakingFreeAll,2:updateReward,
        # 3:withdrawReward,4:unstakingAll,5:stakeReward,>5:nothing
        # what event? we pick one at random (smaller number have higher proba of happening)
        randevent = int(random.expovariate(0.6))
        # who is doing it or concerned?
        randacc = random.randint(0, 9)
        # time elapsed since last event
        timetravel = int(86400 * random.gauss(0.5, 0.2))
        chain.sleep(timetravel)
        print("time lapse =", timetravel / 86400, "days")
        # staking
        if randevent == 0:
            amount = int(random.expovariate(1 / 200000)) * 10 ** 18
            # stakers staking more than 150000 will probably want
            #  to lock the staking to access higher tiers
            if amount > 150000 * 10 ** 18:
                lockduration = random.randint(1, 3) * 2592000
            else:
                lockduration = random.randint(0, 2) * 2592000
            print(
                "accounts[",
                randacc,
                "] stakes ",
                amount,
                "ftg for ",
                lockduration,
                "secs.",
            )
            ftgstaking.stake(
                amount, lockduration, {"from": accounts[randacc]},
            )
        # unstakeFreeAll
        elif randevent == 1:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                ftgstaking.updateBalances(accounts[randacc])
                if ftgstaking.getBalances(accounts[randacc])[2] > 0:
                    print("accounts[", randacc, "] unstakeFreeAll")
                    ftgstaking.unstakeFreeAll({"from": accounts[randacc]})
        # updateReward
        elif randevent == 2:
            if ftgstaking.getBalances(accounts[0])[0] > 0:
                print("accounts[", randacc, "] update Reward")
                ftgstaking.updateReward({"from": accounts[0]})
                rewardsList = ftgstaking.viewRewardsList()
                print("rewardsList=", rewardsList)
        # withdrawReward
        elif randevent == 3:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                print("accounts[", randacc, "] withdraw Reward ")
                ftgstaking.updateReward({"from": accounts[randacc]})
                reward = ftgstaking.getAccountRewardInfo(accounts[randacc])[0]
                if reward != 0:
                    ftgstaking.withdrawReward({"from": accounts[randacc]})
        # unstakeAll
        elif randevent == 4:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                ftgstaking.updateBalances(accounts[randacc])
                if (
                    ftgstaking.getBalances(accounts[randacc])[0]
                    - ftgstaking.getBalances(accounts[randacc])[1]
                    > 0
                ):
                    print("accounts[", randacc, "] unstakeAll")
                    ftgstaking.unstakeAll({"from": accounts[randacc]})
        # stakeReward
        elif randevent == 5:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                ftgstaking.updateReward({"from": accounts[randacc]})
                reward = ftgstaking.getAccountRewardInfo(accounts[randacc])[0]
                if reward != 0:
                    amount = int(random.random() * reward)
                    print("accounts[", randacc, "] stakes", amount, "ftg reward")
                    ftgstaking.stakeReward(amount, 0, {"from": accounts[randacc]})
        # no action
        elif randevent > 5:
            pass
    # display stakings
    print("accounts stacking = (totalStaked, timestamp, amount, lockDuration)")
    for i in range(10):
        staking = ftgstaking.getStakings(accounts[i])
        print("accounts[", i, "]'s stacking = ", staking)
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # calculateAPY
    apy = ftgstaking.calculateAPY.call({"from": accounts[0]})
    print("APY=", 100 * apy / 10 ** 9, "%")

