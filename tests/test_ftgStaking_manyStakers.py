import brownie
import random, math
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

# We want to perform more systematic tests using many stakers taking random actions
def test_ftgStaking_manyStakers(accounts, ftgtoken):
    print("++++++++++++++++test_ftgStaking_manyStakers+++++++++++++++++")
    # initial ftg balances
    assert ftgtoken.balanceOf(accounts[0]) == 210000000 * 10 ** 18
    for i in range(1, 10):
        assert ftgtoken.balanceOf(accounts[i]) == 10000000 * 10 ** 18
    # deploy the contract
    ftgstaking = deploy_FTGStaking(ftgtoken.address, accounts[0])
    # approvals
    ftgtoken.approve(ftgstaking, 210000000 * 10 ** 18, {"from": accounts[0]})
    for i in range(1, 10):
        # approve contract to transfer ftg for accounts[i]
        ftgtoken.approve(ftgstaking, 10000000 * 10 ** 18, {"from": accounts[i]})

    # we consider stakeholders stake at random times normally distributed
    # staked amounts are exponentially distributed from ruby to diamond tiers limit
    for i in range(30):
        # 0:staking,1:unstakingFreeAll,2:rewardDeposit,3:unstakingAll,4:updateReward,
        # 5:stakeReward,6:withdrawReward,>6:nothing
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
            amount = int(random.expovariate(1 / 500000))
            # stakers staking more than 150000 will probably want
            #  to lock the staking to access higher tiers
            if amount > 150000:
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
            print("allowance=", ftgtoken.allowance(accounts[randacc], ftgstaking))
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
        # Reward Deposit by admin
        elif randevent == 2:
            print("1M Reward Deposit!")
            ftgtoken.approve(ftgstaking, 1000000, {"from": accounts[0]})
            ftgstaking.depositRewardTokens(1000000)
        # unstakeAll
        elif randevent == 3:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                ftgstaking.updateBalances(accounts[randacc])
                if (
                    ftgstaking.getBalances(accounts[randacc])[0]
                    - ftgstaking.getBalances(accounts[randacc])[1]
                    > 0
                ):
                    print("accounts[", randacc, "] unstakeAll")
                    ftgstaking.unstakeAll({"from": accounts[randacc]})
        # updateReward
        elif randevent == 4:
            if ftgstaking.getBalances(accounts[0])[0] > 0:
                print("accounts[", randacc, "] update Reward")
                ftgstaking.updateReward({"from": accounts[0]})
                rewardsList = ftgstaking.viewRewardsList()
                print("rewardsList=", rewardsList)
        # stakeReward
        elif randevent == 5:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                ftgstaking.updateReward({"from": accounts[randacc]})
                reward = ftgstaking.getAccountRewardInfo(randacc)[0]
                if reward != 0:
                    amount = int(random.random() * reward)
                    print("accounts[", randacc, "] stakes", amount, "ftg reward")
                    ftgstaking.stakeReward(amount, 0, {"from": accounts[randacc]})
        # withdrawReward
        elif randevent == 6:
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                print("accounts[", randacc, "] withdraw Reward ")
                ftgstaking.updateReward({"from": accounts[randacc]})
                reward = ftgstaking.getAccountRewardInfo(accounts[randacc])[0]
                if reward != 0:
                    ftgstaking.withdrawReward({"from": accounts[randacc]})
        # no action
        elif randevent > 6:
            pass
    # display stakings
    print("accounts stacking = (totalStaked, timestamp, amount, lockDuration)")
    for i in range(10):
        staking = ftgstaking.getStakings(accounts[i])
        print("accounts[", i, "]'s stacking = ", staking)
