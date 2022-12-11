// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";
import "./FTGStaking.sol";
import "./NTT.sol";

/**
 * @title FTGAirdrop
 * @notice This contract is meant to reward eligible FTG Stakers with specific airdropsTokens. The eligibility of
 * a staker will depend on his active locked staking for an eligible lockDuration, and the reward amount will depend
 * on the staking amount of the staker depending on four eligible tiers.
 */

contract FTGAirdrop is Ownable {
    //tiers Memberships
    enum Tiers {
        NONE,
        RUBY,
        SAPPHIRE,
        EMERALD,
        DIAMOND
    }

    //Sale Phases
    enum Phases {
        Setup,
        Distribution,
        Claim
    }

    Phases public airdropPhase;

    uint256 public totalTokensToAirdrop;
    address public stakingContractAddress;
    uint256 public eligibleLockDuration;
    address public airdropToken;

    // factors determining Tiers relative tokens allocation
    mapping(Tiers => uint256) public tiersTokensAllocationFactor;
    // ftg staking threshold for Tiers
    mapping(Tiers => uint256) public tiersMinFTGStaking;

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
        require(airdropPhase == Phases.Setup, "not setup phase");
        eligibleLockDuration = _eligibleLockDuration;
    }

    // function allows owner to set tiers min ftg staking threshold
    // should it really be setup here? does it vary between sales?
    function setTiersMinFTGStakings(
        uint256 _rubyMin,
        uint256 _sapphireMin,
        uint256 _emeraldMin,
        uint256 _diamondMin
    ) public onlyOwner {
        require(airdropPhase == Phases.Setup, "not setup phase");
        require(
            _rubyMin < _sapphireMin &&
                _sapphireMin < _emeraldMin &&
                _emeraldMin < _diamondMin,
            "tiersMinFTGStaking must be increasing from lower to higher tiers"
        );
        tiersMinFTGStaking[Tiers.RUBY] = _rubyMin;
        tiersMinFTGStaking[Tiers.SAPPHIRE] = _sapphireMin;
        tiersMinFTGStaking[Tiers.EMERALD] = _emeraldMin;
        tiersMinFTGStaking[Tiers.DIAMOND] = _diamondMin;
    }

    // set tiers tokens allocation
    function setTiersTokensAllocationFactors(
        uint256 _sapphireAllocationFactor,
        uint256 _emeraldAllocationFactor,
        uint256 _diamondAllocationFactor
    ) public onlyOwner {
        require(airdropPhase == Phases.Setup, "not setup phase");
        require(
            _sapphireAllocationFactor < _emeraldAllocationFactor &&
                _emeraldAllocationFactor < _diamondAllocationFactor,
            "factors must be increasing from lower to higher tiers"
        );
        tiersTokensAllocationFactor[Tiers.RUBY] = 1;
        tiersTokensAllocationFactor[Tiers.SAPPHIRE] = _sapphireAllocationFactor;
        tiersTokensAllocationFactor[Tiers.EMERALD] = _emeraldAllocationFactor;
        tiersTokensAllocationFactor[Tiers.DIAMOND] = _diamondAllocationFactor;
    }
}
