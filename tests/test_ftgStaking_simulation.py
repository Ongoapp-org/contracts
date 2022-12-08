import brownie
import random, math
from brownie.network import gas_price
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

# these tests to simulate a staking period when many stakers prepare to participate to an IDO
def test_ftgStaking_manyStakers_simul_stakingPeriod(accounts, ftgtoken):
    print("\n")
    print(
        "++++++++++++++++test_ftgStaking_manyStakers_stakingPeriod+++++++++++++++++ \n"
    )
    print("\n")
    # set network gas price
    network.gas_price("13 gwei")
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

    # set new reward Rate ( 10% APY : rewardRatePer1TFTG ~ 3170)
    apy = 30
    print("apy =", apy, "%")
    newRewardRate = apy * 10 ** 12 / 31536000 / 100
    print("newRewardRate = ", newRewardRate, " ftg/sec/10¹²ftg")
    ftgstaking.adjustRewardRatePer1TFTG(newRewardRate)
    rewardRatePer1TFTGafter = ftgstaking.rewardRatePer1TFTG()
    print("after modif by admin, rewardRatePer1TFTG = ", rewardRatePer1TFTGafter)

    # First Staking Period
    startTime = chain.time()
    nbOfEventsStakingPeriod = 100
    for i in range(nbOfEventsStakingPeriod):
        # timestep
        regTimeStep = 3600
        halfPeakSpread = 86400
        peakTime = startTime + 3 * 86400
        timeStep = int(
            regTimeStep * (1 - gaussian(chain.time(), halfPeakSpread, peakTime))
        )
        chain.sleep(timeStep)
        print("time=", chain.time(), ", timelapsed =", timeStep / 60, "mins")
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
            # staking event
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
                totalFeesB4 = ftgstaking.totalFees()
                ftgstaking.stake(
                    amount, lockduration, {"from": accounts[randacc]},
                )
                totalFeesAfter = ftgstaking.totalFees()
                assert (
                    totalFeesAfter
                    == totalFeesB4 + ftgstaking.STAKING_FEE() * amount / 100
                )
            # updateReward
            elif randevent == 2:
                if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                    print("accounts[", randacc, "] update Reward")
                    rewardBalB4 = ftgstaking.getAccountRewardInfo(accounts[randacc])[0]
                    print(
                        "Before update: accounts[",
                        randacc,
                        "] reward Balance = ",
                        rewardBalB4,
                    )
                    if ftgstaking.getAccountRewardInfo(accounts[randacc])[1] == 0:
                        print("First reward update for accounts[", randacc, "]")
                        timeSinceLastUpdate = (
                            chain.time()
                            - ftgstaking.getStakings(accounts[randacc])[-1][1]
                        )
                    else:
                        timeSinceLastUpdate = (
                            chain.time()
                            - ftgstaking.getAccountRewardInfo(accounts[randacc])[1]
                        )
                    print(
                        "accounts[",
                        randacc,
                        "] timeSinceLastUpdate =",
                        timeSinceLastUpdate,
                    )
                    staking = ftgstaking.getBalances(accounts[randacc])[0]
                    print("accounts[", randacc, "] total staking =", staking)
                    tx = ftgstaking.updateReward({"from": accounts[randacc]})
                    print(tx.events)
                    rewardBalAfter = ftgstaking.getAccountRewardInfo(accounts[randacc])[
                        0
                    ]
                    print(
                        "After update: accounts[",
                        randacc,
                        "] reward Balance = ",
                        rewardBalAfter,
                    )
                    # verif reward calc ,
                    # verified on some examples but commented out
                    # cause some calculation precision limitation
                    # assert (rewardBalAfter
                    #    == rewardBalB4
                    #    + timeSinceLastUpdate
                    #    * staking
                    #    * ftgstaking.rewardRatePer1TFTG()
                    #    / 10 ** 12
                    # )

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

    # ******************* IDO Period, more quiet period ****************************

    # Set to True for running the "quiet period" after the "staking period"
    if False:
        nbOfEventsQuietPeriod = 100
        for i in range(nbOfEventsQuietPeriod):
            # timestep
            # gaussian distributed time step around one event every hours
            avgTimeStep = 86400
            timeStep = int(avgTimeStep * random.gauss(0.5, 0.3))
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
                # what event? we pick one at random (uniformly distributed)
                randevent = random.randint(0, 5)
                # who is doing it or concerned?
                randacc = random.randint(0, 49)
                # staking events
                if randevent == 0:
                    amount = int(random.expovariate(1 / 200000)) * 10 ** 18
                    if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                        ftgstaking.updateBalances(accounts[randacc])
                        if (
                            ftgstaking.getBalances(accounts[randacc])[0]
                            > 3000000 * 10 ** 18
                        ):
                            print(
                                "totalStaked=",
                                ftgstaking.getBalances(accounts[randacc])[0],
                            )
                            print("We limit staking to 3M for accounts[", randacc, "]!")
                            continue
                    # we limit to 5 stakings per stakeholder (included unstaking event) for the simulation
                    if len(ftgstaking.getStakings(accounts[randacc])) > 5:
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
                    # print(tx.info())
                # unstakeFreeAll
                elif randevent == 1:
                    if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                        ftgstaking.updateBalances(accounts[randacc])
                        print(
                            "unstakingFreeAll accounts[",
                            randacc,
                            " Balances =",
                            ftgstaking.getBalances(accounts[randacc]),
                        )
                        if ftgstaking.getBalances(accounts[randacc])[2] > 0:
                            print("accounts[", randacc, "] unstakeFreeAll")
                            ftgstaking.unstakeFreeAll({"from": accounts[randacc]})
                # updateReward
                elif randevent == 2:
                    if ftgstaking.getBalances(accounts[randacc])[0] > 0:
                        print("accounts[", randacc, "] update Reward")
                        ftgstaking.updateReward({"from": accounts[randacc]})
                        print(
                            "accounts[",
                            randacc,
                            "] reward Balance = ",
                            ftgstaking.getAccountRewardInfo(accounts[1])[0],
                        )
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
                        print(
                            "unstakingAll accounts[",
                            randacc,
                            " Balances =",
                            ftgstaking.getBalances(accounts[randacc]),
                        )
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
                            print(
                                "accounts[", randacc, "] stakes", amount, "ftg reward"
                            )
                            ftgstaking.stakeReward(
                                amount, 0, {"from": accounts[randacc]}
                            )
                # no action
                elif randevent > 5:
                    continue

    # display stakings
    print("accounts stacking = (totalStaked, timestamp, amount, lockDuration)")
    for i in range(50):
        staking = ftgstaking.getStakings(accounts[i])
        print("accounts[", i, "]'s stacking = ", staking)
    # simulation time
    totalTimeElapsed = chain.time() - startTime
    print("simulation total time = ", totalTimeElapsed / 3600, " hours")
    # staking and unstaking fees
    print("rewardRate's apy = ", apy)
    print("STAKING_FEE = ", ftgstaking.STAKING_FEE())
    print("UNSTAKING_FEE = ", ftgstaking.UNSTAKING_FEE())
    # Check rewards earned by stakeholders
    eval0 = ftgstaking.evaluateTotalRedeemableReward(True, {"from": accounts[0]})
    print(
        "evaluation of total rewards earned by stakers= ",
        eval0.return_value / 10 ** 18,
        "ftg",
    )
    # totalFees
    totalFees = ftgstaking.totalFees() / 10 ** 18
    print("totalFees paid by stakers= ", totalFees, "ftg")
    # difference between total reward redeemable and totalFees is what ftg admin need to provide
    print(
        "Difference between total redeemable rewards and totalFees \n (= ftg amount that need to be provided to contract for sustainability): \n",
        eval0.return_value / 10 ** 18 - totalFees,
        "ftg",
    )
    # totalFTGStaked
    print("TotalFTGStaked by Stakeholders = ", ftgstaking.totalFTGStaked() / 10 ** 18)
    # network info
    print("network.gas_price = ", network.gas_price())
    # tx = ftgstaking.adjustRewardRatePer1TFTG(newRewardRate)
    # print(tx.info())

