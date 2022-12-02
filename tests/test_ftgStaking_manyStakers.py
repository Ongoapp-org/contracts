import brownie
import random, math
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

# We want to perform more systematic tests using many stakers taking random actions
def test_ftgStaking_manyStakers_generalCase(accounts, ftgtoken):
    print("\n")
    print("++++++++++++++++test_ftgStaking_manyStakers+++++++++++++++++ \n")
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
    # Scenario of events at random times (time laps between events
    #  normally distributed around some mean time laps). Probability of events
    # is decreasing with increasing label number of the event type.
    #  Most probable event is a random stakeholder stakes random amounts (exponentialy distributed,
    #  higher proba for lower staking amounts), lockduration randomly chosen depending on staking amount
    # (it makes more sense to lock larger amount for longer time (?)). Secondly most probable event is
    #  unstakingFreeAll when a random stakeholder unstake its staking without incuring any fee.
    # Thirdly most probable events are just a reward updates, mostly for testing the rewardUpdate()
    # method since it is the most delicate part of the contract for accurate reward calculation.
    # Next most probable event is the reward withdrawal by a random stakeholder. Then less probable events
    # of unstaking all ftg by a random stakeholder possibly incuring fee. Lastly, most unlikely events
    # are the staking of rewards by a random stakeholder.
    lastDepositTime = chain.time()
    for i in range(100):
        # reward deposit of ftg every week
        if chain.time() - lastDepositTime > 7 * 86400:
            print("Admin Reward Deposit!")
            ftgstaking.depositRewardTokens(10 * 10 ** 18)
            lastDepositTime = chain.time()
        # 0:staking,1:unstakingFreeAll,2:updateReward,
        # 3:withdrawReward,4:unstakingAll,5:stakeReward,>5:nothing
        # what event? we pick one at random (smaller number have higher proba of happening)
        randevent = int(random.expovariate(0.6))
        # who is doing it or concerned?
        randacc = random.randint(0, 9)
        # time elapsed since last event
        timetravel = int(3600 * random.gauss(0.25, 0.1))
        chain.sleep(timetravel)
        print("time lapse =", timetravel / 3600, "hours")
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
            print("hello unstaking")
            if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                ftgstaking.updateBalances(accounts[randacc])
                print("hello2 unstaking", ftgstaking.getBalances(accounts[randacc]))
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
            continue
    # display stakings
    print("accounts stacking = (totalStaked, timestamp, amount, lockDuration)")
    for i in range(10):
        staking = ftgstaking.getStakings(accounts[i])
        print("accounts[", i, "]'s stacking = ", staking)
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # calculateAPY
    avgRewardPer1BFTG = ftgstaking.calculateAvgRewardPer1BFTG.call(
        {"from": accounts[0]}
    )
    apy = round(100 * avgRewardPer1BFTG / 10 ** 9, 2)
    print("APY=", apy, "%")


# this tests to simulate a staking period when many stakers prepare to participate to an IDO
""" def test_ftgStaking_manyStakers_stakingPeriod(accounts, ftgtoken):
    print("\n")
    print(
        "++++++++++++++++test_ftgStaking_manyStakers_stakingPeriod+++++++++++++++++ \n"
    )
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
    # Scenario of events at random times (time laps between events
    #  normally distributed around some mean time laps). Probability of events
    # is decreasing with increasing label number of the event type.
    #  Most probable event is a random stakeholder stakes random amounts (exponentialy distributed,
    #  higher proba for lower staking amounts), lockduration randomly chosen depending on staking amount
    # (it makes more sense to lock larger amount for longer time (?)). Secondly most probable event is
    #  unstakingFreeAll when a random stakeholder unstake its staking without incuring any fee.
    # Thirdly most probable events are just a reward updates, mostly for testing the rewardUpdate()
    # method since it is the most delicate part of the contract for accurate reward calculation.
    # Next most probable event is the reward withdrawal by a random stakeholder. Then less probable events
    # of unstaking all ftg by a random stakeholder possibly incuring fee. Lastly, most unlikely events
    # are the staking of rewards by a random stakeholder.
    # We allow simultaneous events for more realistic scenario and testing updateReward().

    # Gaussian function to simulate gaussian peak of events during staking phase
    def gaussian(x, sigma, mu):
        return math.exp(-(((x - mu) / (math.sqrt(2) * sigma)) ** 2))

    startTime = chain.time()
    lastDepositTime = startTime
    nbOfEventsStakingPeriod = 100
    # First Staking Period
    for i in range(nbOfEventsStakingPeriod):
        # reward deposit of ftg every week
        # almost switch off during staking period since fees are quite high
        rewardDeposit = 1000000 * 10 ** 18
        if chain.time() - lastDepositTime > 7 * 86400:
            print("Admin Reward Deposit!")
            ftgstaking.depositRewardTokens(rewardDeposit)
            lastDepositTime = chain.time()
        # calculateAPY
        if i % 10 == 0:
            if len(ftgstaking.viewRewardsList()) > 1:
                avgRewardPer1BFTG = ftgstaking.calculateAvgRewardPer1BFTG.call(
                    {"from": accounts[0]}
                )
                apy = round(100 * avgRewardPer1BFTG / 10 ** 9, 2)
                print("APY=", apy, "%")
        # timestep
        regTimeStep = 3600
        halfPeakSpread = 86400
        peakTime = startTime + 3 * 86400
        timeStep = int(
            regTimeStep * (1 - gaussian(chain.time(), halfPeakSpread, peakTime))
        )
        chain.sleep(timeStep)
        print("time=", chain.time(), ", timelaps =", timeStep / 60, "mins")
        # simultaneous events allowed once in a while
        simulTimeRand = int(random.expovariate(0.98))
        for j in range(simulTimeRand + 1):
            if j == 1:
                print("HEHOOOO SIMULTANEOUS EVENTS")
            # 0:staking,1:unstakingFreeAll,2:updateReward,
            # 3:withdrawReward,4:unstakingAll,5:stakeReward,>5:nothing
            # what event? we pick one at random (smaller number have higher proba of happening)
            randevent = int(random.expovariate(0.6))
            # who is doing it or concerned?
            randacc = random.randint(0, 49)
            # staking
            if randevent == 0:
                amount = int(random.expovariate(1 / 200000)) * 10 ** 18
                if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                    ftgstaking.updateBalances(accounts[randacc])
                    if (
                        ftgstaking.getBalances(accounts[randacc])[0]
                        > 3000000 * 10 ** 18
                    ):
                        print(
                            "totalStaked=", ftgstaking.getBalances(accounts[randacc])[0]
                        )
                        print("We limit staking to 3M for accounts[", randacc, "]!")
                        continue
                # we limit to 3 stakings per stakeholder (included unstaking event) for the simulation
                if len(ftgstaking.getStakings(accounts[randacc])) > 2:
                    continue
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
            # updateReward
            elif randevent == 2:
                if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                    print("accounts[", randacc, "] update Reward --->")
                    accountReward = ftgstaking.getAccountRewardInfo(accounts[randacc])
                    print("Before update, rewardBalance = ", accountReward)
                    tx = ftgstaking.updateReward({"from": accounts[randacc]})
                    print(tx.events)
                    accountReward = ftgstaking.getAccountRewardInfo(accounts[randacc])
                    print("After update, rewardBalance = ", accountReward)
                    rewardsList = ftgstaking.viewRewardsList()
                    print("rewardsList=", rewardsList)
                    stakings = ftgstaking.getStakings(accounts[randacc])
                    print("stakeholders[accounts[", randacc, "]].stakings=", stakings)
                    sumRewardTimesStakings = 0
                    for k in range(len(rewardsList)):
                        rewardTime = rewardsList[k][2]
                        print("k=", k)
                        for l, staking in reversed(list(enumerate(stakings))):
                            print("l=", l)
                            stakingsTime = stakings[l][1]
                            if rewardTime <= stakingsTime:
                                continue
                            else:
                                print(
                                    "rewardPer1BFTG=",
                                    rewardsList[k][1],
                                    ", totalStaked=",
                                    stakings[l][0],
                                )
                                sumRewardTimesStakings += (
                                    rewardsList[k][1] * stakings[l][0] / 10 ** 9
                                )
                                print(
                                    "sumRewardTimesStakings = ", sumRewardTimesStakings
                                )
                                break
                    print("final sumRewardTimesStakings = ", sumRewardTimesStakings)
                    assert "{:e}".format(sumRewardTimesStakings) == "{:e}".format(
                        accountReward[0]
                    )
            # unstakeAll (some people decide to withdraw their ftg)
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
            # no action
            elif randevent > 5:
                continue

    nbOfEventsQuietPeriod = 100
    # IDO Period, more quiet period
    for i in range(nbOfEventsQuietPeriod):
        # reward deposit of ftg every week
        # must be higher during quiet period
        rewardDeposit = 1000000 * 10 ** 18
        if chain.time() - lastDepositTime > 7 * 86400:
            print("Admin Reward Deposit!")
            ftgstaking.depositRewardTokens(rewardDeposit)
            lastDepositTime = chain.time()
        # calculateAPY
        if i % 10 == 0:
            if len(ftgstaking.viewRewardsList()) > 1:
                avgRewardPer1BFTG = ftgstaking.calculateAvgRewardPer1BFTG.call(
                    {"from": accounts[0]}
                )
                apy = round(100 * avgRewardPer1BFTG / 10 ** 9, 2)
                print("APY=", apy, "%")

        # timestep
        # gaussian distributed time step around one event every hours
        avgTimeStep = 3600
        timeStep = int(avgTimeStep * random.gauss(0.25, 0.1))
        chain.sleep(timeStep)
        print("time=", chain.time(), ", timelaps =", timeStep / 3600, "hours")
        # simultaneous events allowed once in a while
        # keep it for testing purpose
        simulTimeRand = int(random.expovariate(0.98))
        for j in range(simulTimeRand + 1):
            if j == 1:
                print("HEHOOOO SIMULTANEOUS EVENTS")
            # 0:staking,1:unstakingFreeAll,2:updateReward,
            # 3:withdrawReward,4:unstakingAll,5:stakeReward,>5:nothing
            # what event? we pick one at random (smaller number have higher proba of happening)
            randevent = int(random.expovariate(0.6))
            # who is doing it or concerned?
            randacc = random.randint(0, 49)
            # staking
            if randevent == 0:
                amount = int(random.expovariate(1 / 200000)) * 10 ** 18
                if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                    ftgstaking.updateBalances(accounts[randacc])
                    if (
                        ftgstaking.getBalances(accounts[randacc])[0]
                        > 3000000 * 10 ** 18
                    ):
                        print(
                            "totalStaked=", ftgstaking.getBalances(accounts[randacc])[0]
                        )
                        print("We limit staking to 3M for accounts[", randacc, "]!")
                        continue
                # we limit to 3 stakings per stakeholder (included unstaking event) for the simulation
                if len(ftgstaking.getStakings(accounts[randacc])) > 2:
                    continue
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
            # updateReward
            elif randevent == 2:
                if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                    print("accounts[", randacc, "] update Reward --->")
                    accountReward = ftgstaking.getAccountRewardInfo(accounts[randacc])
                    print("Before update, rewardBalance = ", accountReward)
                    tx = ftgstaking.updateReward({"from": accounts[randacc]})
                    print(tx.events)
                    accountReward = ftgstaking.getAccountRewardInfo(accounts[randacc])
                    print("After update, rewardBalance = ", accountReward)
                    rewardsList = ftgstaking.viewRewardsList()
                    print("rewardsList=", rewardsList)
                    stakings = ftgstaking.getStakings(accounts[randacc])
                    print("stakeholders[accounts[", randacc, "]].stakings=", stakings)
                    sumRewardTimesStakings = 0
                    for k in range(len(rewardsList)):
                        rewardTime = rewardsList[k][2]
                        print("k=", k)
                        for l, staking in reversed(list(enumerate(stakings))):
                            print("l=", l)
                            stakingsTime = stakings[l][1]
                            if rewardTime <= stakingsTime:
                                continue
                            else:
                                print(
                                    "rewardPer1BFTG=",
                                    rewardsList[k][1],
                                    ", totalStaked=",
                                    stakings[l][0],
                                )
                                sumRewardTimesStakings += (
                                    rewardsList[k][1] * stakings[l][0] / 10 ** 9
                                )
                                print(
                                    "sumRewardTimesStakings = ", sumRewardTimesStakings
                                )
                                break
                    print("final sumRewardTimesStakings = ", sumRewardTimesStakings)
                    assert "{:e}".format(sumRewardTimesStakings) == "{:e}".format(
                        accountReward[0]
                    )
            # unstakeAll (some people decide to withdraw their ftg)
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
            # no action
            elif randevent > 5:
                continue

    # display stakings
    print("accounts stacking = (totalStaked, timestamp, amount, lockDuration)")
    for i in range(50):
        staking = ftgstaking.getStakings(accounts[i])
        print("accounts[", i, "]'s stacking = ", staking)
    # Check rewardsList
    rewardsList = ftgstaking.viewRewardsList()
    print("rewardsList=", rewardsList)
    # simulation time
    totalTimeElapsed = chain.time() - startTime
    print("simulation total time = ", totalTimeElapsed / 3600, " hours")
    # calculateAPY
    avgRewardPer1BFTG = ftgstaking.calculateAvgRewardPer1BFTG.call(
        {"from": accounts[0]}
    )
    apy = round(100 * avgRewardPer1BFTG / 10 ** 9, 2)
    print("APY=", apy, "%") """

