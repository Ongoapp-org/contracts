// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";
import "./FTGStaking.sol";
import "./NTT.sol";

/**
 * @title FTGAirdrop
 * @notice This contract is meant to reward eligible FTG Stakers with specific airdropsTokens. The eligibility of
 * a staker will depend on his active locked staking for an eligible lockDuration, set by the airdrop admin before
 * the airdrop, and the reward will be proportional to the staking amount of the staker.
 */

contract FTGAirdrop is Ownable {
    uint256 public totalTokensToAirdrop;
    address public stakingContractAddress;
    uint256 public eligibleLockDuration;
    address public airdropToken;

    event airdrop(address _airdropToken, uint256 _totalTokensToAirdrop);
    event Log(string message, uint256 data);
    event LogAddress(string message, address data);

    constructor(
        address _airdropToken,
        address _stakingContractAddress,
        uint256 _totalTokensToAirdrop
    ) {
        airdropToken = _airdropToken;
        stakingContractAddress = _stakingContractAddress;
        totalTokensToAirdrop = _totalTokensToAirdrop;
    }

    //********************* Setup Phase functions *********************/

    // set staking eligible lockDuration for owner
    function setEligibleLockDuration(uint256 _eligibleLockDuration)
        public
        onlyOwner
    {
        eligibleLockDuration = _eligibleLockDuration;
    }

    //********************* Distribution Phase functions *********************/

    function launchAirdrop() public onlyOwner {
        address[] memory participantsAddresses = IFTGStaking(
            stakingContractAddress
        ).getStakeholdersAddresses();
        uint256[] memory eligibleActiveStakingLocked = new uint256[](
            participantsAddresses.length
        );
        uint256 totalEligibleActiveStakingLocked;
        uint256 activeStakingLocked;
        for (uint256 i = 0; i < participantsAddresses.length; i++) {
            activeStakingLocked = uint256(
                IFTGStaking(stakingContractAddress)
                    .checkParticipantLockedStaking(
                        participantsAddresses[i],
                        eligibleLockDuration
                    )
            );
            totalEligibleActiveStakingLocked += activeStakingLocked;
            eligibleActiveStakingLocked[i] = activeStakingLocked;
        }
        //airdrop tokens to participants
        uint256 airdropAmount;
        for (uint256 i = 0; i < participantsAddresses.length; i++) {
            airdropAmount = PRBMath.mulDiv(
                eligibleActiveStakingLocked[i],
                totalTokensToAirdrop,
                totalEligibleActiveStakingLocked
            );
            IERC20(airdropToken).transfer(
                participantsAddresses[i],
                airdropAmount
            );
        }
        emit airdrop(airdropToken, totalTokensToAirdrop);
    }

    // function to deposit airdrop tokens on airdrop contract
    function depositAirdropTokens(uint256 _amount) external onlyOwner {
        // Transfer of airdrop token to the airdrop Contract (contract need to be approved first)
        IERC20(airdropToken).transferFrom(msg.sender, address(this), _amount);
    }
}
