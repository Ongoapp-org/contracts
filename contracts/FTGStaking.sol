//!COPIED FRMO last change

// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/access/Ownable.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";

/**
 * @title FTGStaking
 * @notice Rewards for Stakeholders come from fees (initial staking fee, before 30 days unstaking fee)
 * or rewards deposited by admin. Rewards are gained depending on the amount staked by stakeholder.
 * Reward is not compounded, it is accumulated in a separate balance, but can be moved to staking using stakeReward().
 * Stakeholders incur a fee of 15% for unstaking before 30 days. Staking can be locked for 30, 60 or 90 days
 * and stakeholder receive special privileges during allocation for this. Rewards and Balances are updated
 * only when needed and last update times recorded.
 */

interface IFTGStaking {
    function checkParticipantLockedStaking(
        address _participantAddress,
        uint256 lockDurationChecked
    ) external view returns (int256 lockedStakingTotal);
}

contract FTGStaking is Ownable {
    IERC20 public immutable ftgToken;

    uint256 constant INITIAL_STAKING_FEE = 5; // %
    uint256 constant UNSTAKING_FEE = 15; // %

    // Staking Tiers
    // StakeType not used, replaced by stakingDuration
    // enum StakeType {
    //     FLEX,
    //     LOCK30DAYS,
    //     LOCK60DAYS,
    //     LOCK90DAYS
    // }

    struct Stakeholder {
        uint256 totalStaked; // current total ftg staking of the stakeholder
        uint256 totalLockedBalance; // current total ftg locked (for 30,60 or 90 days)
        uint256 freeToUnstakeBalance; // current part of the staked ftg that are free to unstake without incurring fee
        uint256 lastBalancesUpdate; // last time totalLockedBalance and freeToUnstakeBalance were updated
        uint256 totalReward; // total reward accumulated by the stakeholder
        uint256 lastRewardUpdate; // last time totalReward was updated
        Staking[] stakings; // list of staking (positive amount) or unstaking (negative amount) by a stakeholder
    }

    // New staking or unstaking
    struct Staking {
        uint256 totalStaked; // totalStaked after this staking
        uint256 timestamp; // time of staking
        int256 amount; // amount of staking (>0 staking, <0 unstaking)
        uint256 lockDuration; // duration of locked time in secs (flex = 0, LOCK30DAYS = 2592000, LOCK60DAYS = 5184000, LOCK90DAYS = 7776000)
    }

    // New reward (deposit or fee)
    struct Reward {
        uint256 rewards; // incoming reward distributed to stakeholders
        uint256 rewardPer1BFTG; // mean reward for 1 billion ftg
        uint256 timestamp; // time when reward was deposited
    }

    uint256 public totalFTGStaked; // contract's total amount of FTG staked

    Reward[] public rewardsList; // list of reward events

    mapping(address => Stakeholder) public stakeholders; // list of stakeholders

    event NewStake(
        address indexed user,
        uint256 amount,
        uint256 lockDuration,
        uint256 timestamp
    );
    event NewUnstake(address indexed user, uint256 amount, uint256 timestamp);
    event NewReward(uint256 indexed amount, uint256 timestamp);
    //event For debugging
    event Log(string message, uint256 data);
    event Logint(string message, int256 data);

    constructor(address _stakingToken) {
        ftgToken = IERC20(_stakingToken);
    }

    // To register a new reward deposit or fee
    function _addNewReward(uint256 _reward) private {
        if (totalFTGStaked != 0) {
            emit Log("_reward", _reward);
            uint256 rewardPer1BFTG = PRBMath.mulDiv(
                1_000_000_000, // multiplier for calculation precision
                _reward,
                totalFTGStaked
            );
            emit Log("rewardPer1BFTG", rewardPer1BFTG);
            rewardsList.push(Reward(_reward, rewardPer1BFTG, block.timestamp));
            emit NewReward(_reward, block.timestamp);
        } else {
            rewardsList.push(Reward(_reward, 0, block.timestamp));
            emit NewReward(_reward, block.timestamp);
        }
    }

    // to retrieve the first reward index to add from last updated time
    function _getfirstRewardsIndexToAdd(uint256 lastUpdateTime)
        private
        view
        returns (uint256)
    {
        uint256 i = rewardsList.length > 0 ? rewardsList.length - 1 : 0;
        /* emit Log("i0=",i);
        emit Log("rewardsList[i].timestam",rewardsList[i].timestamp); */
        while (rewardsList[i].timestamp >= lastUpdateTime && i != 0) {
            unchecked {
                --i;
            }
            // emit Log("i=",i);
        }
        return i > 0 ? i + 1 : 1;
    }

    // to retrieve the stakeholder's stake at a certain reward time
    function _getStakeHolderStakeIndexBeforeTime(
        address _stakeholderAddress,
        uint256 _time
    ) private view returns (uint256) {
        uint256 len = stakeholders[_stakeholderAddress].stakings.length;
        uint256 i = len > 0 ? len - 1 : 0;
        while (
            stakeholders[_stakeholderAddress].stakings[i].timestamp > _time &&
            i != 0
        ) {
            unchecked {
                --i;
            }
        }
        return i > 0 ? i : 0;
    }

    // to update the reward balance of a stakeholder
    function _updateStakeholderReward(address _stakeholderAddress) private {
        uint256 startIndex = _getfirstRewardsIndexToAdd(
            stakeholders[_stakeholderAddress].lastRewardUpdate
        );
        emit Log("startIndex=", startIndex);
        uint256 rewardsSum = 0;
        for (uint256 i = startIndex; i < rewardsList.length; i++) {
            uint256 stakeholderStakeIndexAtRewardTime = _getStakeHolderStakeIndexBeforeTime(
                    _stakeholderAddress,
                    rewardsList[i].timestamp
                );
            emit Log(
                "stakeholderStakeIndexAtRewardTime=",
                stakeholderStakeIndexAtRewardTime
            );
            uint256 stakeholderStakeAtRewardtime = stakeholders[
                _stakeholderAddress
            ].stakings[stakeholderStakeIndexAtRewardTime].totalStaked;
            emit Log(
                "stakeholderStakeAtRewardtime=",
                stakeholderStakeAtRewardtime
            );
            emit Log(
                "rewardsList[i].rewardPer1BFTG=",
                rewardsList[i].rewardPer1BFTG
            );
            rewardsSum += PRBMath.mulDiv(
                rewardsList[i].rewardPer1BFTG,
                stakeholderStakeAtRewardtime,
                1_000_000_000 // multiplier for calculation precision
            );
            emit Log("rewardsSum=", rewardsSum);
        }
        emit Log("final rewardsSum=", rewardsSum);
        stakeholders[_stakeholderAddress].totalReward += rewardsSum;
        stakeholders[_stakeholderAddress].lastRewardUpdate = block.timestamp;
    }

    // public function to update Rewards
    function updateReward() public {
        require(
            stakeholders[msg.sender].stakings.length != 0,
            "Not a stakeholder!"
        );
        _updateStakeholderReward(msg.sender);
    }

    // stake ftg token
    function stake(uint256 _amount, uint256 _lockDuration) public {
        require(
            _lockDuration <= 365 days,
            "can not stake longer than 365 days"
        );
        // Check that user does not stake 0
        require(_amount > 0, "Cannot stake nothing");
        // Check staker's balance is enough
        require(
            _amount < ftgToken.balanceOf(msg.sender),
            "Insufficient FTG Balance"
        );

        // Transfer of ftg token to the staking Contract (contract need to be approved first)
        ftgToken.transferFrom(msg.sender, address(this), _amount);

        // first staking ?
        uint256 fee;
        if (stakeholders[msg.sender].stakings.length == 0) {
            // calculate initial fee
            fee = PRBMath.mulDiv(INITIAL_STAKING_FEE, _amount, 100);
            _addNewReward(fee);
        }
        uint256 amountStaked = _amount - fee;
        // Add stake's amount to stakeholder's totalStaked
        stakeholders[msg.sender].totalStaked += amountStaked;
        totalFTGStaked += amountStaked;
        emit Log("totalFTGStaked", totalFTGStaked);

        // TODO comment
        if (_lockDuration == 0) {
            // Add the new Stake to the stakeholder's stakes List
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    int256(amountStaked),
                    0
                )
            );
            // Emit a NewStake event
            emit NewStake(msg.sender, amountStaked, 0, block.timestamp);
        } else if (_lockDuration >= 30 days) {
            // Add the new Stake to the stakeholder's stakes List
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    int256(amountStaked),
                    _lockDuration
                )
            );
            //increase totalLockedBalance
            stakeholders[msg.sender].totalLockedBalance += amountStaked;
            // Emit a NewStake event
            emit NewStake(
                msg.sender,
                amountStaked,
                _lockDuration,
                block.timestamp
            );
        }
        //
    }

    // function to update the freeToUnstakeBalance and totalLockedBalance
    function _updateStakeholderBalances(address _stakeholderAddress) private {
        // We get staking index just after last freeToUnstakeBalance update
        uint256 StakingIndexBeforeTime = _getStakeHolderStakeIndexBeforeTime(
            _stakeholderAddress,
            stakeholders[_stakeholderAddress].lastBalancesUpdate
        );
        uint256 indexToStartUpdate = StakingIndexBeforeTime > 0
            ? StakingIndexBeforeTime + 1
            : 0;
        emit Log("indexToStartUpdate = ", indexToStartUpdate);
        uint256 stakingslen = stakeholders[_stakeholderAddress].stakings.length;
        // check if stakings after last update time are free to unstake
        for (uint256 i = indexToStartUpdate; i < stakingslen; i++) {
            Staking memory _staking = stakeholders[_stakeholderAddress]
                .stakings[i];
            if (_staking.lockDuration == 0) {
                // in case we deal with flex staking
                if (block.timestamp - _staking.timestamp > 30 days) {
                    stakeholders[_stakeholderAddress]
                        .freeToUnstakeBalance += uint256(_staking.amount); //staking._amount should be >0
                }
            } else {
                // in case we deal with locked Staking
                if (
                    block.timestamp - _staking.timestamp > _staking.lockDuration
                ) {
                    // lockTime finished, update totalLockedBalance
                    stakeholders[_stakeholderAddress]
                        .totalLockedBalance -= uint256(_staking.amount);
                    stakeholders[_stakeholderAddress]
                        .freeToUnstakeBalance += uint256(_staking.amount);
                }
            }
        }
        // update lastBalancesUpdate
        stakeholders[_stakeholderAddress].lastBalancesUpdate = block.timestamp;
    }

    // unstake ftg
    function unstake(uint256 _amount) public {
        // verify that stakeholder has staking
        require(stakeholders[msg.sender].totalStaked != 0, "No FTG staked");
        // update stakeholder's balances
        _updateStakeholderBalances(msg.sender);
        // calculate not locked stacking balance
        uint256 totalNotLocked = stakeholders[msg.sender].totalStaked -
            stakeholders[msg.sender].totalLockedBalance;
        // verifies that staking can be unstaked
        require(totalNotLocked > 0, "nothing to unstake");
        require(_amount <= totalNotLocked, "withdrawable amount exceeded");
        // unstake less than whats free to unstake
        if (_amount <= stakeholders[msg.sender].freeToUnstakeBalance) {
            // no fee to unstake
            // stakeholder is only partly withdrawing his staking balance
            stakeholders[msg.sender].totalStaked -= _amount;
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    -int256(_amount),
                    0
                )
            );
            stakeholders[msg.sender].freeToUnstakeBalance -= _amount;
            totalFTGStaked -= _amount;
            // transfer to stakeholder
            ftgToken.transfer(msg.sender, _amount);
            emit NewUnstake(msg.sender, _amount, block.timestamp);
        } else {
            // if amount exceeds totalStaked, we withdraw everything and apply fee
            stakeholders[msg.sender].totalStaked -= _amount;
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    -int256(_amount),
                    0
                )
            );
            // reset freeToUnstakeBalance to zero
            stakeholders[msg.sender].freeToUnstakeBalance = 0;
            totalFTGStaked -= _amount;
            // unstaking fee
            uint256 amountCharged = _amount -
                stakeholders[msg.sender].freeToUnstakeBalance;
            uint256 fee = PRBMath.mulDiv(UNSTAKING_FEE, amountCharged, 100);
            _addNewReward(fee);
            // transfer to stakeholder
            ftgToken.transfer(msg.sender, _amount - fee);
            emit NewUnstake(msg.sender, _amount, block.timestamp);
        }
        // update LastBalancesUpdate to avoid counting unstake in next BalancesUpdate
        stakeholders[msg.sender].lastBalancesUpdate = block.timestamp;
    }

    // function for the stakeholder to withdraw his accumulated rewards
    function withdrawReward() public {
        // firstly update reward balance
        _updateStakeholderReward(msg.sender);
        // transfer rewards to stakeholder's account
        uint256 rewardToWithdraw = stakeholders[msg.sender].totalReward;
        stakeholders[msg.sender].totalReward = 0;
        ftgToken.transfer(msg.sender, rewardToWithdraw);
    }

    // function for the stakeholder to stake his accumulated rewards
    //TODO more explain how this is used
    function stakeReward(uint256 _amount, uint256 _lockDuration) public {
        require(
            _amount <= stakeholders[msg.sender].totalReward,
            "reward Balance exceeded"
        );
        // firstly update reward balance
        _updateStakeholderReward(msg.sender);
        // transfer reward balance to the staking balance
        stakeholders[msg.sender].totalReward -= _amount;
        stakeholders[msg.sender].totalStaked += _amount;
        stakeholders[msg.sender].stakings.push(
            Staking(
                stakeholders[msg.sender].totalStaked,
                block.timestamp,
                int256(_amount),
                _lockDuration
            )
        );
    }

    // returns the rewardsList array
    function viewRewardsList() public view returns (Reward[] memory) {
        return rewardsList;
    }

    // returns the stakeholder's stakings array
    function getStakings(address _stakeholderAddress)
        public
        view
        returns (Staking[] memory)
    {
        return stakeholders[_stakeholderAddress].stakings;
    }

    // returns stakeholder's balances
    function getBalances(address _stakeholderAddress)
        public
        view
        returns (
            uint256,
            uint256,
            uint256,
            uint256
        )
    {
        return (
            stakeholders[_stakeholderAddress].totalStaked,
            stakeholders[_stakeholderAddress].totalLockedBalance,
            stakeholders[_stakeholderAddress].freeToUnstakeBalance,
            stakeholders[_stakeholderAddress].lastBalancesUpdate
        );
    }

    // returns the stakeholder's last updated reward
    function getAccountRewardInfo(address _stakeholderAddress)
        public
        view
        returns (uint256, uint256)
    {
        return (
            stakeholders[_stakeholderAddress].totalReward,
            stakeholders[_stakeholderAddress].lastRewardUpdate
        );
    }

    // returns total active locked Staking of an sale participant
    function checkParticipantLockedStaking(
        address _participantAddress,
        uint256 lockDurationChecked
    ) external view returns (int256 lockedStakingTotal) {
        Staking[] memory participantStakings = stakeholders[_participantAddress]
            .stakings;
        for (uint256 i = 0; i < participantStakings.length; i++) {
            //emit Logint("lockedStakingtotal=", lockedStakingTotal);
            if (
                // check if staking is still active and was locked for more than lockDurationChecked
                participantStakings[i].lockDuration >= lockDurationChecked &&
                (block.timestamp <
                    participantStakings[i].timestamp +
                        participantStakings[i].lockDuration)
            ) {
                // add this staking to checkedStakingTotal
                lockedStakingTotal += participantStakings[i].amount;
            }
        }
        return lockedStakingTotal;
    }

    // function to deposit reward
    function depositRewardTokens(uint256 _amount) external onlyOwner {
        _addNewReward(_amount);
        // Transfer of ftg token to the staking Contract (contract need to be approved first)
        ftgToken.transferFrom(msg.sender, address(this), _amount);
    }

    function depositRewardTokensNoUpdate(uint256 _amount) external onlyOwner {
        ftgToken.transferFrom(msg.sender, address(this), _amount);
    }

    // emergency withdraw
    function withdrawRewardTokens(uint256 _amount) external onlyOwner {
        ftgToken.transfer(msg.sender, _amount);
    }
}
