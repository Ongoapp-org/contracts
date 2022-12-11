// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";
import "./FTGStaking.sol";
import "./NTT.sol";

/**
 * @title FTGAirdrop
 * @notice This contract is meant to reward eligible FTG Stakers with regular airdrops. The eligibility of the stakers
 * to a specific airrops depends on his locked staking.
 */

contract FTGAirdrop is Ownable {
    uint256 public totalTokensToAirdrop;
    address public stakingContractAddress;
    address public airdropToken;

    constructor(
        address _airdropToken,
        address _stakingContractAddress,
        uint256 _totalTokensToAirdrop
    ) {
        airdropToken = _investToken;
        stakingContractAddress = _stakingContractAddress;
        totalTokensToAirdrop = _totalTokensToAirdrop;
    }
}
