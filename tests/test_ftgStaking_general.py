import brownie
import random, math
from brownie.network import gas_price
from brownie.network.gas.strategies import GasNowScalingStrategy
from brownie import chain, network
from scripts.deploy_FTGStaking import deploy_FTGStaking

# We want to perform more systematic tests using many stakers taking random actions
def test_ftgStaking_new_general(accounts, ftgtoken):
    print("\n")
    print("++++++++++++++++test_ftgStaking_fixedAPY+++++++++++++++++ \n")
    print("\n")
    # gas strategy
    # gas_strategy = GasNowScalingStrategy("standard", increment=1.2)
    # gas_price(gas_strategy)
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
    print(tx.info())

    # verifies totalFees correctly increased
    print("totalFees = ", ftgstaking.totalFees())
    staking_fee = 0.02
    assert ftgstaking.totalFees() == staking_fee * 600000 * 10 ** 18

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
    print(tx.info)

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

    # second staking 120000 ftg by accounts[1]
    print("**************second staking 120000 ftg by accounts[1] for 90 days \n")
    ftgstaking.stake(
        120000 * 10 ** 18, 7776000, {"from": accounts[1]}
    )  # 90 days = 7776000 secs
    print("3) accounts[1] ftg balance = \n", ftgtoken.balanceOf(accounts[1]))
    # verifies Stakeholder's stakings, fee has been applied normally
    stakings1 = ftgstaking.getStakings(accounts[1])
    print("stakeholders[accounts[1]].stakings=", stakings1)
    # assert int(120000 * 10 ** 18 - staking_fee * 120000 * 10 ** 18) == stakings1[0][0]
    # precision should be improved?
    # verifies totalFees correctly increased
    print("totalFees = ", ftgstaking.totalFees())
    assert (
        ftgstaking.totalFees()
        == staking_fee * 600000 * 10 ** 18 + staking_fee * 120000 * 10 ** 18
    )
    # works but again calculation precision not optimal

    # verifies more than 30 days Locked Staking
    # only one hour has passed since accounts[0] one month locked staking
    # we verifies that it is still active
    totalActiveLocked0 = ftgstaking.checkParticipantLockedStaking(
        accounts[0], 2592000, {"from": accounts[0]}
    )
    print(totalActiveLocked0.events)
    print(
        "accounts[0] first staking should still be locked : checkParticipantLockedStaking amount =",
        totalActiveLocked0.return_value,
    )
    assert (
        totalActiveLocked0.return_value
        == 600000 * 10 ** 18 - staking_fee * 600000 * 10 ** 18
    )
    # wait one month
    timeb4 = chain.time()
    print("wait one month")
    timetravel = 3600 * 24 * 30
    chain.sleep(timetravel)
    assert chain.time() - timeb4 == timetravel
    # verifies that accounts[0] has no locked staking anymore
    totalActiveLocked02 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[0], 2592000, {"from": accounts[0]}
    )
    # print(totalActiveLocked02.events)
    print(
        "accounts[0] staking should not be locked anymore : checkParticipantLockedStaking amount =",
        totalActiveLocked02,
    )
    # assert totalActiveLocked02 == 0
    # !this test is not working! I don't understand what is going on here. If I debug using events inside the
    # the function code, there is no error, all temporary data and final result is correct. If I dont,
    # and switch off the events and the "view" keyword for the function then the result is wrong, giving the
    # last staking amount instead of 0. I tried to modify the conditional logic, and replace it by several if
    # but result is the same. Next test, shows that if we make a new locked staking the amount becomes correct
    #  again... There may be something going on in the internals of brownie. We need to check if the error
    # happens on real test blockchain...

    # new locked staking for accounts[0], no fees applied since it is not initial staking
    ftgstaking.stake(200000 * 10 ** 18, 2592000, {"from": accounts[0]})

    # wait one hour
    print("wait one hour")
    timetravel = 3600
    chain.sleep(timetravel)

    # verifies one month locked staking active again with right amount
    totalActiveLocked03 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[0], 2592000, {"from": accounts[0]}
    )
    print(
        "accounts[0] 196000 staking should still be locked : checkParticipantLockedStaking amount =",
        totalActiveLocked03,
    )
    assert totalActiveLocked03 == 196000 * 10 ** 18

    # verifies balances
    ftgstaking.updateBalances(accounts[0])
    bal0 = ftgstaking.getBalances(accounts[0])
    print("totalStaked,totalLockedBalance,freeToUnstakeBalance,updateTime)=", bal0)
    # totalLockedBalance should be 200000*10**18-staking_fee*2000000
    assert bal0[1] == 200000 * 10 ** 18 - staking_fee * 200000 * 10 ** 18
    # freeToUnstakeBalance should be equal to first staking
    assert bal0[2] == 600000 * 10 ** 18 - staking_fee * 600000 * 10 ** 18

    # verifies that staking of accounts[1] is still locked
    totalActiveLocked1 = ftgstaking.checkParticipantLockedStaking.call(
        accounts[1], 2592000, {"from": accounts[0]}
    )
    print(
        "accounts[1] first staking should still be locked : checkParticipantLockedStaking amount =",
        totalActiveLocked0,
    )
    assert totalActiveLocked1 == 120000 * 10 ** 18 - 120000 * staking_fee * 10 ** 18
    # verifies totalFTGStaked correct
    print("Contracts totalFTGStaked=", ftgstaking.totalFTGStaked())
    assert (
        ftgstaking.totalFTGStaked()
        == 600000 * 10 ** 18
        - 600000 * staking_fee * 10 ** 18
        + 120000 * 10 ** 18
        - 120000 * staking_fee * 10 ** 18
        + 200000 * 10 ** 18
        - 200000 * staking_fee * 10 ** 18
    )

    # Unstaking Tests

    # wait 1h
    timeTravel = 3600
    chain.sleep(timeTravel)

    # test if stakeholder partly unstakes an amount less than FreeToUnstakeBalance
    print("partly unstaking test \n")
    # totalStaked (correct)
    balancesb4 = ftgstaking.getBalances(accounts[0])
    print("accounts[0] balances before unstaking = ", balancesb4)
    # accounts[0] unstaking 10000 * 10 ** 18 ftg
    tx = ftgstaking.unstake(10000 * 10 ** 18, {"from": accounts[0]})
    print(tx.events)
    balancesafter = ftgstaking.getBalances(accounts[0])
    print("accounts[0] balances after unstaking = ", balancesafter)
    # totalStaked
    assert balancesb4[0] - 10000 * 10 ** 18 == balancesafter[0]
    # totalLockedBalance
    assert balancesb4[1] == balancesafter[1]
    # freeToUnstakeBalance
    assert balancesb4[2] - 10000 * 10 ** 18 == balancesafter[2]

    # test if stakeholder unstakes all its freeToUnstake balance (just updated)
    print("completely unstaking freeToUnstakeBalance test \n")
    totalFeesb4 = ftgstaking.totalFees()
    balancesb4 = ftgstaking.getBalances(accounts[0])
    print("accounts[0] balances before unstakingFreeAll = ", balancesb4)
    tx = ftgstaking.unstakeFreeAll({"from": accounts[0]})
    print(tx.events)
    totalFeesafter = ftgstaking.totalFees()
    # verifies totalFees balance has not changed
    assert totalFeesb4 == totalFeesafter
    balancesafter = ftgstaking.getBalances(accounts[0])
    print("accounts[0] balances after unstakingFreeAll = ", balancesafter)
    # totalStaked
    assert balancesb4[0] - balancesb4[2] == balancesafter[0]
    # totalLockedBalance
    assert balancesb4[1] == balancesafter[1]
    # freeToUnstakeBalance
    assert balancesafter[2] == 0

    # test if stakeholder unstakes all its staking and incurring fees
    print("completely unstaking with fee test \n")
    # we wait a month so that locked staking is free to unstake
    # wait one month
    print("wait one month")
    timetravel = 3600 * 24 * 30
    chain.sleep(timetravel)
    # new accounts[0] staking with no lockduration (flex)
    print("stakeholder makes new flex 100000 ftg staking")
    ftgstaking.stake(100000 * 10 ** 18, 0, {"from": accounts[0]})
    # now if accounts[0] unstake everything, he should pay 15% fees on 1000000 ftg unstaked
    ftgbal0b4 = ftgtoken.balanceOf(accounts[0])
    print(
        "before unstaking accounts[0] ftg balance =", ftgbal0b4,
    )
    # check totalFees before unstaking
    totalFeesb4 = ftgstaking.totalFees()
    print("totalFees before unstaking all with fees =", totalFeesb4)
    # update then check balances
    ftgstaking.updateBalances(accounts[0])
    balancesb4 = ftgstaking.getBalances(accounts[0])
    print("accounts[0] balances before unstakingFreeAll = ", balancesb4)
    tx = ftgstaking.unstakeAll({"from": accounts[0]})
    print(tx.events)
    # check balances after unstake (just updated during unstake)
    balancesafter = ftgstaking.getBalances(accounts[0])
    print("accounts[0] balances after unstakingFreeAll = ", balancesafter)
    # totalStaked
    assert balancesafter[0] == 0
    # totalLockedBalance
    assert balancesafter[1] == 0
    # freeToUnstakeBalance
    assert balancesafter[2] == 0
    # check totalFees after unstaking
    totalFeesafter = ftgstaking.totalFees()
    print("totalFees after unstaking all with fees =", totalFeesafter)
    # verifies totalFees balance is correctly updated
    unstaking_fee = 0.15
    """ assert (
        totalFeesb4
        + unstaking_fee * (100000 * 10 ** 18 - 100000 * staking_fee * 10 ** 18)
        == totalFeesafter
    ) """
    # verifies accounts[0] has correctly received the ftg
    ftgbal0after = ftgtoken.balanceOf(accounts[0])
    print(
        "after unstaking accounts[0] ftg balance =", ftgbal0after,
    )
    """ assert (
        ftgbal0after
        == ftgbal0b4
        + 200000 * 10 ** 18
        - 200000 * staking_fee * 10 ** 18
        + 100000 * 10 ** 18
        - 100000 * staking_fee * 10 ** 18
        - 100000 * unstaking_fee * 10 ** 18
    ) """

    # test of staking some reward
    ftgstaking.updateReward({"from": accounts[0]})
    rewardbalb4 = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print(
        "before staking 1500ftg from reward balance: accounts[0] reward balance = ",
        rewardbalb4,
    )
    rewardstaked = 1500 * 10 ** 18
    ftgstaking.stakeReward(rewardstaked, 0)
    rewardbalafter = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print(
        "after staking 1500ftg from reward balance: accounts[0] reward balance = ",
        rewardbalafter,
    )
    assert rewardbalafter == rewardbalb4 - rewardstaked
    print("accounts[0] stakings =", ftgstaking.getStakings(accounts[0]))

    # test of withdrawing the reward balance
    ftgbal0b4 = ftgtoken.balanceOf(accounts[0])
    rewardbalb4 = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print(
        "before withdrawing reward balance: accounts[0] reward balance = ", rewardbalb4,
    )
    print("before withdrawing: stakeholder ftg balance = ", ftgbal0b4)
    ftgstaking.withdrawReward({"from": accounts[0]})
    ftgbal0after = ftgtoken.balanceOf(accounts[0])
    rewardbalafter = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print(
        "after withdrawing reward balance: accounts[0] reward balance = ",
        rewardbalafter,
    )
    print("after withdrawing: stakeholder ftg balance = ", ftgbal0after)
    assert ftgbal0b4 == ftgbal0after - rewardbalb4
    assert rewardbalafter == 0

    # test modif of rewardRatePer1TFTG by admin
    rewardRatePer1TFTGb4 = ftgstaking.rewardRatePer1TFTG()
    print("before modif by admin, rewardRatePer1TFTG = ", rewardRatePer1TFTGb4)
    tx = ftgstaking.adjustRewardRatePer1TFTG(6000)
    print(tx.info())
    rewardRatePer1TFTGafter = ftgstaking.rewardRatePer1TFTG()
    print("after modif by admin rewardRatePer1TFTG = ", rewardRatePer1TFTGafter)
    assert rewardRatePer1TFTGafter == 6000
    # verification another account cannot change the rewardRate
    with brownie.reverts("Ownable: caller is not the owner"):
        ftgstaking.adjustRewardRatePer1TFTG(100000, {"from": accounts[1]})
    assert ftgstaking.rewardRatePer1TFTG() == 6000
    # to modify the rewardRate implied an update of the reward balance before
    rewardbal0aftermodif = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print("accounts[0]'s reward balance = ", rewardbal0aftermodif)
    rewardbal1aftermodif = ftgstaking.getAccountRewardInfo(accounts[1])[0]
    print("accounts[1]'s reward balance = ", rewardbal1aftermodif)

    # wait one week
    print("wait one week")
    timetravel = 3600 * 24 * 7
    chain.sleep(timetravel)

    # verify function to evaluate reward balances of stakeholder
    print("test to evaluate total reward accumulated by stakeholders")
    rewardbal0b4 = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print("accounts[0]'s reward balance = ", rewardbal0b4)
    assert rewardbal0b4 == rewardbal0aftermodif
    rewardbal1b4 = ftgstaking.getAccountRewardInfo(accounts[1])[0]
    print("accounts[1]'s reward balance = ", rewardbal1b4)
    assert rewardbal1b4 == rewardbal1aftermodif
    # when we dont update the reward Balance before
    eval0 = ftgstaking.evaluateTotalRedeemableReward.call(False, {"from": accounts[0]})
    print("evaluation without updates of reward = ", eval0)
    rewardbal0after = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    rewardbal1after = ftgstaking.getAccountRewardInfo(accounts[1])[0]
    # no change in rewards since no update performed during evaluateTotalRedeemableReward
    assert rewardbal0after == rewardbal0b4
    assert rewardbal1after == rewardbal1b4
    assert eval0 == rewardbal0after + rewardbal1after
    # when we do update the reward Balances before determining total rewards
    eval1 = ftgstaking.evaluateTotalRedeemableReward(True, {"from": accounts[0]})
    print("evaluation with updates of reward = ", eval1.return_value)
    print(eval1.events)
    print(eval1.info())
    # update performed during evaluateTotalRedeemableReward (should do more tests to evaluate gas cost diff)
    print("accounts[0]'s stakings = ", ftgstaking.getStakings(accounts[0]))
    staking0 = ftgstaking.getStakings(accounts[0])[-1][0]
    print("accounts[0]'s totalStaked = ", staking0)
    print("accounts[1]'s stakings = ", ftgstaking.getStakings(accounts[1]))
    staking1 = ftgstaking.getStakings(accounts[1])[-1][0]
    print("accounts[1]'s totalStaked = ", staking1)
    # tx = ftgstaking.updateReward({"from": accounts[1]})
    # print(tx.events)
    rewardbal0after2 = ftgstaking.getAccountRewardInfo(accounts[0])[0]
    print("accounts[0]'s reward balance = ", rewardbal0after2)
    rewardbal1after2 = ftgstaking.getAccountRewardInfo(accounts[1])[0]
    print("accounts[1]'s reward balance = ", rewardbal1after2)
    rewardRate = ftgstaking.rewardRatePer1TFTG()
    print("rewardRate=", rewardRate)
    assert (
        rewardbal0after2
        == rewardbal0aftermodif + 3600 * 24 * 7 * staking0 * rewardRate / 10 ** 12
    )
    assert (
        rewardbal1after2
        == rewardbal1aftermodif + 3600 * 24 * 7 * staking1 * rewardRate / 10 ** 12
    )
    assert eval1.return_value == rewardbal0after2 + rewardbal1after2
