// SPDX-License-Identifier: MIT
pragma solidity ^0.8;

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


contract FtgStaking is Ownable {

    IERC20 public immutable ftgToken;

    struct Stake{
        uint256 amount;
        uint256 since;
    }
    
    struct Stakeholder{
        uint256 totalStaked;
        Stake[] stakes;
    }

    mapping(address => Stakeholder) internal stakeholders;

    uint256 public ContractTotalStaked;

    event NewStake(address indexed user, uint256 amount, uint256 timestamp);

    constructor(address _stakingToken, address _rewardToken) {
        ftgToken = IERC20(_stakingToken);
    }

    function stake(uint256 _amount) public {
        // Check that user does not stake 0 
        require(_amount > 0, "Cannot stake nothing");
        // Check staker's balance is enough
        require(_amount < ftgToken.balanceOf(msg.sender), "Insufficient Balance");

        // Transfer and Updates 
        ftgToken.transferFrom(msg.sender, address(this), _amount);
        stakeholders[msg.sender].totalStaked += _amount;
        //Add stake to the contract's total staked
        ContractTotalStaked += _amount;
        //Add the new Stake to the stakes of the stakeholder 
        stakeholders[msg.sender].stakes.push(Stake(_amount,block.timestamp));

        // Emit a NewStake event
        emit NewStake(msg.sender, _amount, block.timestamp);
    }

    // Should we have a reward rate, should we do compounded reward?
    function unstake(uint256 _index, uint256 _amount) public {
        require(_amount <= stakeholders[msg.sender].stakes[_index].amount, "")

    }

}