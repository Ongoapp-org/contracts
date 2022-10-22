// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/access/Ownable.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";

contract FTGStaking is Ownable {
    IERC20 public immutable ftgToken;

    uint256 constant INITIAL_STAKING_FEE = 5; // %
    uint256 constant UNSTAKING_FEE = 15; // %

    // Staking Tiers
    enum StakeType {
        FLEX,
        LOCK30DAYS,
        LOCK60DAYS,
        LOCK90DAYS
    }

    //Can be new stake or unstake
    //amount is negative for unstake
    struct Staking {
        uint256 totalStaked;
        uint256 timestamp;
        int256 amount;
        uint256 lockDuration;
    }

    struct Stakeholder {
        uint256 totalStaked;
        uint256 totalLockedBalance;
        uint256 FreeToUnstakeBalance;
        uint256 lastBalancesUpdate;
        uint256 totalReward;
        uint256 lastRewardUpdate;
        Staking[] stakings;
    }

    struct Reward {
        uint256 rewards;
        uint256 rewardPer1BFTG;
        uint256 timestamp;
    }

    uint256 public totalFTGStaked;

    Reward[] public rewardsList;

    mapping(address => Stakeholder) public stakeholders;

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

    // function to deposit reward
    function depositReward(uint256 _amount) external onlyOwner {
        _addNewReward(_amount);
        // Transfer of ftg token to the staking Contract (contract need to be approved first)
        ftgToken.transferFrom(msg.sender, address(this), _amount);
    }

    // public function to update Rewards
    function updateReward() public {
        _updateStakeholderReward(msg.sender);
    }

    // stake ftg token
    function stake(uint256 _amount, uint256 _lockDuration) public {
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

        if (_lockDuration == 0) {
            // Add the new Stake to the stakeholder's stakes List
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    amountStaked,
                    0
                )
            );
            // Emit a NewStake event
            emit NewStake(msg.sender, amountStaked, 0, block.timestamp);
        } else if (
            _lockDuration == 30 || _lockDuration == 60 || _lockDuration == 90
        ) {
            // Add the new Stake to the stakeholder's stakes List
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    amountStaked,
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

    // function to update the FreeToUnstakeBalance and totalLockedBalance
    function _updateStakeholderBalances(address _stakeholderAddress) public {
        // We get staking index just after last FreeToUnstakeBalance update
        uint256 startIndexToUpdate = _getStakeHolderStakeIndexBeforeTime(
            _stakeholderAddress,
            stakeholders[_stakeholderAddress].lastBalancesUpdate
        ) + 1;
        emit Log("startIndexToUpdate=", startIndexToUpdate);
        uint256 stakingslen = stakeholders[_stakeholderAddress].stakings.length;
        // check if stakings after last update time are free to unstake
        for (uint256 i = startIndexToUpdate; i < stakingslen - 1; i++) {
            Staking _staking = stakeholders[_stakeholderAddress].stakings[i];
            if (_staking.lockDuration == 0) {
                // in case we deal with flex staking
                if (block.timestamp - _staking.timestamp > 30 days) {
                    stakeholders[_stakeholderAddress]
                        .FreeToUnstakeBalance += _staking.amount;
                }
            } else {
                // in case we deal with locked Staking
                if (
                    block.timestamp - _staking.timestamp > _staking.lockDuration
                ) {
                    // lockTime finished, update totalLockedBalance
                    stakeholders[_stakeholderAddress]
                        .totalLockedBalance -= _staking.amount;
                    stakeholders[_stakeholderAddress]
                        .FreeToUnstakeBalance += _staking.amount;
                }
            }
        }
        // update lastBalancesUpdate
        stakeholders[_stakeholderAddress].lastBalancesUpdate = block.timestamp;
    }

    // function called by stakeholder to unstake ftg
    function unstake(uint256 _amount) public {
        // verify that stakeholder has staking
        require(stakeholders[msg.sender].totalStaked != 0, "No FTG staked");
        // update stakeholder's balances
        _updateStakeholderBalances(msg.sender);
        uint256 totalNotLocked = stakeholders[msg.sender].totalStaked -
            stakeholders[msg.sender].totalLockedBalance;
        // if amount exceeds totalStaked, we withdraw everything?
        if (_amount <= stakeholders[msg.sender].FreeToUnstakeBalance) {
            // no fee to unstake
            // stakeholder is only partly withdrawing his staking balance
            stakeholders[msg.sender].totalStaked -= _amount;
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    -_amount,
                    0
                )
            );
            totalFTGStaked -= _amount;
            // transfer to stakeholder
            ftgToken.transfer(msg.sender, _amount);
            emit NewUnstake(msg.sender, _amount, block.timestamp);
        } else {
            //fee applies to unstake that exceeds freeToUnstakeBalance
            if (_amount >= totalNotLocked) {
                //stakeholder is completely withdrawing his unlocked staking
                stakeholders[msg.sender].totalStaked = stakeholders[msg.sender]
                    .totalLockedBalance;
                stakeholders[msg.sender].stakings.push(
                    Staking(
                        stakeholders[msg.sender].totalStaked,
                        block.timestamp,
                        -totalNotLocked,
                        0
                    )
                );
                totalFTGStaked -= totalNotLocked;
                // unstaking fee
                uint256 amountCharged = totalNotLocked -
                    stakeholders[msg.sender].FreeToUnstakeBalance;
                uint256 fee = PRBMath.mulDiv(UNSTAKING_FEE, amountCharged, 100);
                _addNewReward(fee);
                // transfer to stakeholder
                ftgToken.transfer(msg.sender, totalNotLocked - fee);
                emit NewUnstake(
                    msg.sender,
                    stakeholders[msg.sender].totalNotLocked,
                    block.timestamp
                );
            } else {
                //stakeholder is only partly withdrawing his staking balance
                stakeholders[msg.sender].totalStaked -= _amount;
                stakeholders[msg.sender].stakings.push(
                    Staking(
                        stakeholders[msg.sender].totalStaked,
                        block.timestamp,
                        -_amount,
                        0
                    )
                );
                totalFTGStaked -= _amount;
                // unstaking fee
                uint256 amountCharged = _amount -
                    stakeholders[msg.sender].FreeToUnstakeBalance;
                uint256 fee = PRBMath.mulDiv(UNSTAKING_FEE, amountCharged, 100);
                _addNewReward(fee);
                // transfer to stakeholder
                ftgToken.transfer(msg.sender, _amount - fee);
                emit NewUnstake(msg.sender, _amount, block.timestamp);
            }
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
    function stakeReward(uint256 _amount) public {
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
            Staking(stakeholders[msg.sender].totalStaked, block.timestamp)
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
}
