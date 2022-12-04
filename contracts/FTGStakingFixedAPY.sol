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

contract FTGStakingFixedAPY is Ownable {
    IERC20 public immutable ftgToken;

    uint256 constant INITIAL_STAKING_FEE = 15; // %
    uint256 constant UNSTAKING_FEE = 15; // %

    uint256 rewardPer1BFTG = 10**8; // 10% Interest on staking (= fixed APY)

    //StakeHolder are registered in stakeholders when they stake for the first time
    struct Stakeholder {
        uint256 totalStaked; // current total ftg staking of the stakeholder
        uint256 totalLockedBalance; // current total ftg locked (for 30 days or more)
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

    uint256 public totalFTGStaked; // contract's total amount of FTG staked
    uint256 public totalFees; //protocol's fees (initial staking, before 30 days unstaking)

    /* Reward[] public rewardsList; // list of reward events */

    mapping(address => Stakeholder) public stakeholders; // list of stakeholders

    //prorocol's events
    event NewStake(
        address indexed user,
        uint256 amount,
        uint256 lockDuration,
        uint256 timestamp
    );
    event NewUnstake(address indexed user, uint256 amount, uint256 timestamp);
    event NewFee(uint256 indexed amount, uint256 timestamp);

    //event For debugging
    event Log(string message, uint256 data);
    event Logint(string message, int256 data);

    //constructor
    constructor(address _stakingToken) {
        ftgToken = IERC20(_stakingToken);
    }

    // to update the reward balance of a stakeholder
    // need to be call before any staking or unstaking
    function _updateStakeholderReward(address _stakeholderAddress) private {
        // We verify first that the address corresponds to an actual stakeholder
        require(
            stakeholders[_stakeholderAddress].stakings.length != 0,
            "Not a stakeholder!"
        );
        //Looking for rewards since the last reward update
        uint256 lastRewardUpdate = stakeholders[_stakeholderAddress]
            .lastRewardUpdate;
        uint256 timeSinceLastUpdate = block.timestamp - lastRewardUpdate;
        uint256 staking = stakeholders[_stakeholderAddress].totalStaked;
        uint256 newReward = PRBMath.mulDiv(
            31536000, // = 1 year in secs
            rewardPer1BFTG * staking,
            timeSinceLastUpdate * 1_000_000_000
        );
        stakeholders[_stakeholderAddress].totalReward += newReward;
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
        require(
            _lockDuration == 0 || _lockDuration >= 30 days,
            "LockDuration is 0 or at least one month"
        );
        // Check that user does not stake 0
        require(_amount > 0, "Cannot stake nothing");
        // Check if staker's balance is enough
        require(
            _amount < ftgToken.balanceOf(msg.sender),
            "Insufficient FTG Balance"
        );

        // Transfer of ftg token to the staking Contract (contract need to be approved first)
        ftgToken.transferFrom(msg.sender, address(this), _amount);

        //We update stakeholder's Reward Balance before
        //necessary before any change in stakeholder's totalStaked
        _updateStakeholderReward(msg.sender);

        // first staking ?
        uint256 fee;
        if (stakeholders[msg.sender].stakings.length == 0) {
            // calculate initial fee
            fee = PRBMath.mulDiv(INITIAL_STAKING_FEE, _amount, 100);
            totalFees += fee;
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
    }

    // function to update the freeToUnstakeBalance and totalLockedBalance
    function _updateStakeholderBalances(address _stakeholderAddress) private {
        // We verify first that the address corresponds to an actual stakeholder
        require(
            stakeholders[_stakeholderAddress].stakings.length != 0,
            "Not a stakeholder!"
        );
        //use temporary variable to avoid writing to storage multiple times
        uint256 freeToUnstakeBalTemp;
        uint256 totalLockedBalTemp;
        for (
            uint256 i = 0;
            i < stakeholders[_stakeholderAddress].stakings.length;
            i++
        ) {
            Staking memory _staking = stakeholders[_stakeholderAddress]
                .stakings[i];
            int256 amount = _staking.amount;
            if (_staking.lockDuration == 0) {
                // in case we deal with flex staking
                if (amount < 0) {
                    //we deal with an unstaking event
                    uint256 amountpos = uint256(-amount);
                    if (amountpos <= freeToUnstakeBalTemp) {
                        freeToUnstakeBalTemp -= amountpos;
                    } else {
                        freeToUnstakeBalTemp = 0;
                    }
                } else {
                    //we deal with a staking event
                    if (block.timestamp - _staking.timestamp > 30 days) {
                        freeToUnstakeBalTemp += uint256(amount);
                    }
                }
            } else {
                // in case we deal with locked Staking
                if (
                    block.timestamp - _staking.timestamp > _staking.lockDuration
                ) {
                    //lockTime finished
                    freeToUnstakeBalTemp += uint256(amount);
                } else {
                    //staking still locked
                    totalLockedBalTemp += uint256(amount);
                }
            }
        }
        stakeholders[_stakeholderAddress]
            .freeToUnstakeBalance = freeToUnstakeBalTemp;
        stakeholders[_stakeholderAddress]
            .totalLockedBalance = totalLockedBalTemp;
        // update lastBalancesUpdate
        stakeholders[_stakeholderAddress].lastBalancesUpdate = block.timestamp;
    }

    function unstakeFreeAll() public {
        require(
            stakeholders[msg.sender].stakings.length != 0,
            "Not a stakeholder!"
        );
        _updateStakeholderBalances(msg.sender);
        uint256 amount = stakeholders[msg.sender].freeToUnstakeBalance;
        unstake(amount);
    }

    function unstakeAll() public {
        require(
            stakeholders[msg.sender].stakings.length != 0,
            "Not a stakeholder!"
        );
        _updateStakeholderBalances(msg.sender);
        uint256 amount = stakeholders[msg.sender].totalStaked -
            stakeholders[msg.sender].totalLockedBalance;
        unstake(amount);
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
        emit Log("totalNotLocked=", totalNotLocked);
        // verifies that staking can be unstaked
        require(totalNotLocked > 0, "nothing to unstake");
        require(_amount <= totalNotLocked, "withdrawable amount exceeded");
        //We update stakeholder's Reward Balance
        //necessary before any change in stakeholder's totalStaked
        _updateStakeholderReward(msg.sender);
        // unstake less than what is free to unstake
        if (_amount <= stakeholders[msg.sender].freeToUnstakeBalance) {
            // no fee to unstake
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
            // if amount exceeds FreeToUnstakeBalance, fee is applied
            stakeholders[msg.sender].totalStaked -= _amount;
            stakeholders[msg.sender].stakings.push(
                Staking(
                    stakeholders[msg.sender].totalStaked,
                    block.timestamp,
                    -int256(_amount),
                    0
                )
            );
            totalFTGStaked -= _amount;
            // unstaking fee
            uint256 amountCharged = _amount -
                stakeholders[msg.sender].freeToUnstakeBalance;
            uint256 fee = PRBMath.mulDiv(UNSTAKING_FEE, amountCharged, 100);
            totalFees += fee;
            // reset freeToUnstakeBalance to zero
            stakeholders[msg.sender].freeToUnstakeBalance = 0;
            // transfer to stakeholder
            ftgToken.transfer(msg.sender, _amount - fee);
            emit NewUnstake(msg.sender, _amount, block.timestamp);
        }
        // update LastBalancesUpdate since balances have just been updated
        stakeholders[msg.sender].lastBalancesUpdate = block.timestamp;
    }

    // function for the stakeholder to withdraw his/her accumulated rewards
    function withdrawReward() public {
        require(
            stakeholders[msg.sender].stakings.length != 0,
            "Not a stakeholder!"
        );
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

    function updateBalances(address _stakeholderAddress) public {
        _updateStakeholderBalances(_stakeholderAddress);
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
    // Need to call updateStakeholderBalances() before for up to date balances
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

    //average rewardPer1BFTG over one year
    function calculateTotalRedeemableReward() public returns (uint256) {
        require(rewardsList.length > 1, "No Rewards yet");
        uint256 time = rewardsList[rewardsList.length - 1].timestamp -
            rewardsList[0].timestamp;
        uint256 rewardPer1BFTGSum;
        for (uint256 i = 0; i < rewardsList.length; i++) {
            rewardPer1BFTGSum += rewardsList[i].rewardPer1BFTG;
        }
        //one year in secs = 31536000
        //very first reward due to init Staking of first stakeholder not counted
        emit Log("rewardPer1BFTGSum", rewardPer1BFTGSum);
        uint256 avgRewardPer1BFTG = PRBMath.mulDiv(
            1,
            rewardPer1BFTGSum,
            rewardsList.length - 1
        );
        emit Log("avgRewardPer1BFTG", avgRewardPer1BFTG);
        return avgRewardPer1BFTG;
    }

    // returns total active locked Staking of an sale participant
    function checkParticipantLockedStaking(
        address _participantAddress,
        uint256 lockDurationChecked
    ) external view returns (int256 lockedStakingTotal) {
        require(
            stakeholders[_participantAddress].stakings.length != 0,
            "Not a stakeholder!"
        );
        Staking[] memory participantStakings = stakeholders[_participantAddress]
            .stakings;
        for (uint256 i = 0; i < participantStakings.length; i++) {
            /* emit Logint("lockedStakingtotal=", lockedStakingTotal);
            emit Log("block.timestamp=", block.timestamp);
            emit Log(
                "participantStakings[i].timestamp=",
                participantStakings[i].timestamp
            );
            emit Log(
                "participantStakings[i].lockDuration=",
                participantStakings[i].lockDuration
            ); */
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
        // Transfer of ftg token to the staking Contract (contract need to be approved first)
        ftgToken.transferFrom(msg.sender, address(this), _amount);
    }

    // emergency withdraw
    function withdrawRewardTokens(uint256 _amount) external onlyOwner {
        ftgToken.transfer(msg.sender, _amount);
    }
}
