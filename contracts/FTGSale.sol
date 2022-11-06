// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";

import "./FTGStaking.sol";

//https://github.com/avalaunch-app/xava-protocol/blob/master/contracts/sales/AvalaunchSale.sol

//TODO handle 2 pools
//Guaranteed Pool
//Public Pool
contract FTGSale is Ownable {

    struct Participant {
        address partaddr;
        uint256 amountAllocated;
        uint256 amountInvested;
    }

    // TODO move this is duplicate
    // New staking or unstaking
    struct Staking {
        uint256 totalStaked; // totalStaked after this staking
        uint256 timestamp; // time of staking
        int256 amount; // amount of staking (>0 staking, <0 unstaking)
        uint256 lockDuration; // duration of locked time in secs (flex = 0, LOCK30DAYS = 2592000, LOCK60DAYS = 5184000, LOCK90DAYS = 7776000)
    }

    public enum Tiers {
        DIAMOND,
        EMERALD,
        SAPPHIRE,
        RUBY,
        NONE
    }

    string nameSale;

    mapping(address => Participant) public participants;

    mapping(address => bool) public whitelist;
    //all ticket allocated for each tier
    mapping(Tiers => uint32) tiersAllocated;
    //used ticket for each tier
    mapping(Tiers => uint32) ticketAllocated;

    // Token being sold
    IERC20 saleToken;
    // invest token
    IERC20 investToken;
    // Is sale created
    bool isCreated;
    // Are earnings withdrawn
    bool earningsWithdrawn;
    // Is leftover withdrawn
    bool leftoverWithdrawn;
    // Have tokens been deposited
    bool tokensDeposited;
    // Address of sale owner
    address saleOwner;
    // Price of the token quoted in ETH
    uint256 tokenPriceInETH;
    // Amount of tokens to sell
    uint256 amountOfTokensToSell;
    // Total tokens being sold
    uint256 totalTokensSold;
    // Total ETH Raised
    uint256 totalETHRaised;
    // Sale end time
    uint256 saleEnd;
    // Price of the token quoted in USD
    uint256 tokenPriceInUSD;

    FTGStaking stakingContract;
    uint256 diamondMinimum = 1_000_000;
    uint256 emeraldMinimum = 500_000;
    uint256 sapphireMinimum = 250_000;
    uint256 rubyMinimum = 100_000;

    uint32 eachDiamondTicket;
    uint32 eachEmeraldTicket;
    uint32 eachSapphireTicket;
    uint32 eachRubyTicket;

    //TODO make a setting
    uint32 diamondParticipants = 100;
    uint32 emeraldParticipants = 500;
    uint32 sapphireParticipants = 1000;
    uint32 rubyParticipants = 2000;

    //TODO make a setting
    uint256 amountGuaranteedPool = 1_000_000;
    uint256 amountPublicPool = 500_000;
    uint32 factor = 10_000;

    //TODO make a setting
    uint32 diamondAllocTotal = 40;
    uint32 emeraldAllocTotal = 30;
    uint32 sapphireAllocTotal = 20;
    uint32 rubyAllocTotal = 10;

    constructor(
        string memory _name,
        address _stakingContractAddress,
        uint256 _amountGuaranteedPool,
        uint256 _tokenPriceInUSD
    ) {
        //TODO in constructor
        
        tiersAllocated[Tiers.DIAMOND] = 40 * factor;
        tiersAllocated[Tiers.EMERALD] = 30 * factor;
        tiersAllocated[Tiers.SAPPHIRE] = 20 * factor;
        tiersAllocated[Tiers.RUBY] = 10 * factor;

        eachDiamondTicket = tiersAllocated[Tiers.DIAMOND] / diamondParticipants;
        eachEmeraldTicket = tiersAllocated[Tiers.EMERALD] / emeraldParticipants;
        eachSapphireTicket =
            tiersAllocated[Tiers.SAPPHIRE] /
            sapphireParticipants;
        eachRubyTicket = tiersAllocated[Tiers.RUBY] / rubyParticipants;

        nameSale = _name;
        stakingContract = FTGStaking(_stakingContractAddress);
        amountGuaranteedPool = _amountGuaranteedPool;
        tokenPriceInUSD = _tokenPriceInUSD;
    }

    // TODO calculate amount eligible
    function amountEligible(address account) private returns (uint256) {
        return 0;
    }

    function _checkStaking() private {
        //calculate amount staked in 30 days or more
        //subtract amount from available pool
        //amountGuaranteedPool -= participantAmount;
    }

    function addWhitelist(address p) external onlyOwner {
        whitelist[p] = true;

        //TODO other steps?
    }

    //checkParticipationSignature

    //take part in the sale i.e buy tokens, pass signature on frontend
    function participate(uint256 amountTokensBuy) external {
        //TODO which pool

        require(whitelist[msg.sender], "not in whitelist");
        //determine allocation size
        uint256 amountElig = amountEligible(msg.sender);
        require(amountTokensBuy <= amountElig, "amount too high not eliglbe");

        // bytes calldata signature
        // signature verifies KYC

        //price is fixed

        uint256 costInUSD = amountTokensBuy * tokenPriceInUSD;
        IERC20(investToken).transferFrom(msg.sender, address(this), costInUSD);

        IERC20(saleToken).transfer(msg.sender, amountTokensBuy);
    }

    // Function for owner to deposit tokens
    //function depositTokens() onlyOwner {}

    //TODO
    //function withdrawLeftOverTokens() onlyOwner {}

    //TODO
    //function withdrawRaisedAssets() onlyOwner {}

    // mapping(Tiers => uint128) participants = [];

    // function manipulatetiersAllocated(Tiers tier) public {
    //     if (tier == Tiers.DIAMOND) {} else if (
    //         tier == Tiers.EMERALD
    //     ) {} else if (tier == Tiers.SAPPHIRE) {} else if (tier == Tiers.RUBY) {}
    // }

    // function getStakeHohders(address add)
    //     public
    //     returns (
    //         uint256 totalStaked,
    //         uint256 totalLockedBalance,
    //         uint256 freeToUnstakeBalance,
    //         uint256 lastBalancesUpdate,
    //         uint256 totalReward,
    //         uint256 lastRewardUpdate
    //     )
    // {
    //     return (stakingContract.stakeholders(add));
    // }

    //memberShipTickets
    // tiersAllocated[Tiers.RUBY] -= eachDiamondTicket;
    // ticketAllocated[Tiers.RUBY] +=                        
    //     eachDiamondTicket;
}
