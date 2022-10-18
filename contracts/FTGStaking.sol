// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";
import "./Ownable.sol";


interface IERC20 {
    function totalSupply() external view returns (uint);

    function balanceOf(address account) external view returns (uint);

    function transfer(address recipient, uint amount) external returns (bool);

    function allowance(address owner, address spender) external view returns (uint);

    function approve(address spender, uint amount) external returns (bool);

    function transferFrom(
        address sender,
        address recipient,
        uint amount
    ) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);
}


contract FTGStaking is Ownable {

    IERC20 public immutable ftgToken;

    //Can be new stake or unstake 
    struct StakeChange{
        uint256 totalStaked;
        uint256 timestamp;
    }
    
    struct Stakeholder{
        uint256 totalStaked;
        uint256 totalReward;
        uint256 lastRewardUpdate;
        StakeChange[] flexStakes;
    }

    struct Reward{
        uint256 rewards;
        uint256 rewardPerFTG;
        uint256 timestamp;
    }

    uint256 totalFTGStaked;

    enum StakeType { FLEX, LOCK30DAYS }

    Reward[] public rewardsList;

    mapping(address => Stakeholder) internal stakeholders;

    event NewStake(address indexed user, uint256 amount, uint256 timestamp);
    event NewReward(uint256 indexed amount, uint256 timestamp);

    constructor(address _stakingToken) {
        ftgToken = IERC20(_stakingToken);
    }

    // To register a new reward deposit or fee
    function _addNewReward(uint256 _reward, uint256 _timestamp) internal {
        if (totalFTGStaked!=0){
            uint256 rewardPerFTG = PRBMath.mulDiv(1, _reward, totalFTGStaked);
            rewardsList.push(Reward(_reward,rewardPerFTG,block.timestamp));
        }else{
            rewardsList.push(Reward(_reward,0,block.timestamp));
        }
    }

    // to retrieve the rewards from a certain time
    function _getRewardsIndexfromTime(uint256 lastUpdateTime) internal view returns(uint256) { 
        uint256 i = rewardsList.length > 0 ? rewardsList.length -1 : 0;
        while(rewardsList[i].timestamp >= lastUpdateTime) {
            unchecked {
                --i;
            }
        return i > 0 ? i : 0;
        } 
    }

    // to retrieve the stakeholder's stake at a certain time
    function _getStakeHolderStakeIndexFromTime(address _stakeholderAddress, uint256 _time) internal view returns(uint256) { 
        uint256 i = stakeholders[_stakeholderAddress].flexStakes.length > 0 ? stakeholders[_stakeholderAddress].flexStakes.length-1 : 0;
        while(stakeholders[_stakeholderAddress].flexStakes[i].timestamp >= _time) {
            unchecked {
                --i;
            }
        return i > 0 ? i : 0;
        } 
    }

    // to update the reward balance of a stakeholder
    function _updateStakeholderReward(address _stakeholderAddress, StakeType _stakeType) internal {
        if (_stakeType == StakeType.FLEX) {
            uint256 startIndex = _getRewardsIndexfromTime(stakeholders[_stakeholderAddress].lastRewardUpdate)+1;
            uint256 rewardsSum = 0;
            for (uint256 i=startIndex;i<rewardsList.length-1;i++){
                uint256 stakeholderStakeIndex = _getStakeHolderStakeIndexFromTime(_stakeholderAddress,rewardsList[i].timestamp);
                uint256 stakeholderStake = stakeholders[_stakeholderAddress].flexStakes[stakeholderStakeIndex].totalStaked;
                rewardsSum +=  rewardsList[i].rewardPerFTG * stakeholderStake ;
            }
            stakeholders[_stakeholderAddress].totalReward += rewardsSum;
            stakeholders[_stakeholderAddress].lastRewardUpdate = block.timestamp;
        }
    }


    // function called by stakeholder to stake ftg 
    function stake(uint256 _amount, StakeType _stakeType) public {

        // Check that user does not stake 0 
        require(_amount > 0, "Cannot stake nothing");
        // Check staker's balance is enough
        require(_amount < ftgToken.balanceOf(msg.sender), "Insufficient FTG Balance");


        // Transfer of ftg token to the staking Contract
        ftgToken.transferFrom(msg.sender, address(this), _amount);

        if (_stakeType == StakeType.FLEX) {
            // first staking ?
            uint256 fee;
            if (stakeholders[msg.sender].flexStakes.length == 0) {
                // add stakeholder
                //stakeholders[_address].push(Stakeholder(0,0,block.timestamp,[]));
                // calculate initial fee
                fee = PRBMath.mulDiv(5, _amount, 100);
                _addNewReward(fee, block.timestamp);
            }
            uint256 amountStaked = _amount-fee;
            // Add stake's amount to stakeholder's totalStaked
            stakeholders[msg.sender].totalStaked += amountStaked;
            totalFTGStaked += amountStaked;
            // Calculate Stakeholder's totalReward
            //stakeholders[msg.sender].totalReward = _updateStakeholderReward(msg.sender,StakeType.FLEX);
            // Update lastRewardUpdate
            //stakeholders[msg.sender].lastRewardUpdate = block.timestamp;
            // Add the new Stake to the stakeholder's stakes List 
            stakeholders[msg.sender].flexStakes.push(StakeChange(stakeholders[msg.sender].totalStaked, block.timestamp));

            // Emit a NewStake event
            emit NewStake(msg.sender, amountStaked, block.timestamp);
        }
    }

    function depositReward(uint256 _amount) external {
         _addNewReward(_amount, block.timestamp);
    }

    function updateReward() public {
        _updateStakeholderReward(msg.sender,StakeType.FLEX);
    }

   /*  function unstake(uint256 _index, uint256 _amount) public {
        //require(_amount > stakeholders[msg.sender].stakes[_index].amount, "Requested amount exceeds staked amount");
        if (stakeholders[msg.sender].stakes[_index].amount <= _amount) {
            //actually removing entry from stakes array would be gas costly
            delete stakeholders[msg.sender].stakes[_index];
            uint256 actualAmount = stakeholders[msg.sender].stakes[_index].amount;
            stakeholders[msg.sender].totalStaked -= actualAmount;
            ContractTotalStaked -= actualAmount;
            ftgToken.transfer(msg.sender, actualAmount);
        } else {
            stakeholders[msg.sender].stakes[_index].amount -=_amount;
            stakeholders[msg.sender].totalStaked -= _amount;
            ContractTotalStaked -= _amount;
            ftgToken.transfer(msg.sender, _amount);
        }
    } */

    // returns the rewardsList array
    function getRewardsList() public view returns (Reward[] memory) {
        return rewardsList;
    }

    // returns the stakeholder's flexStakes array
    function getStakes(address _stakeholderAddress) public view returns (StakeChange[] memory) {
        return stakeholders[_stakeholderAddress].flexStakes;
    }

     // returns the stakeholder's last updated reward
    function getAccountRewardInfo(address _stakeholderAddress) public view returns (uint256,uint256) {
        return (stakeholders[_stakeholderAddress].totalReward,stakeholders[_stakeholderAddress].lastRewardUpdate);
    }
 
    // returns total FTG Staked on contract
    function getTotalFTGStaked() public view returns (uint256) {
        return totalFTGStaked;
    }

}