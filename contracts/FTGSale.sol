// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";

import "./FTGStaking.sol";

//https://github.com/avalaunch-app/xava-protocol/blob/master/contracts/sales/AvalaunchSale.sol

//
//2 pools
//Guaranteed Pool
//Public Pool
contract FTGSale is Ownable {
    struct Participant {
        address partaddr;
        uint256 amountAllocated;
    }

    // TODO move this is duplicate
    // New staking or unstaking
    struct Staking {
        uint256 totalStaked; // totalStaked after this staking
        uint256 timestamp; // time of staking
        int256 amount; // amount of staking (>0 staking, <0 unstaking)
        uint256 lockDuration; // duration of locked time in secs (flex = 0, LOCK30DAYS = 2592000, LOCK60DAYS = 5184000, LOCK90DAYS = 7776000)
    }

    enum Tiers {
        DIAMOND,
        EMERALD,
        SAPPHIRE,
        RUBY
    }

    string nameSale;

    mapping(address => Participant) public participants;

    mapping(address => bool) public whitelist;
    //all ticket alocated for each tier
    mapping(Tiers => uint32) allAllocated;
    //used ticket for each tocket
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
    uint8 factor = 10_000;

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
        
        allAllocated[Tiers.DIAMOND] = 40 * factor;
        allAllocated[Tiers.EMERALD] = 30 * factor;
        allAllocated[Tiers.SAPPHIRE] = 20 * factor;
        allAllocated[Tiers.RUBY] = 10 * factor;

        eachDiamondTicket = allAllocated[Tiers.DIAMOND] / diamondParticipants;
        eachEmeraldTicket = allAllocated[Tiers.EMERALD] / emeraldParticipants;
        eachSapphireTicket =
            allAllocated[Tiers.SAPPHIRE] /
            sapphireParticipants;
        eachRubyTicket = allAllocated[Tiers.RUBY] / rubyParticipants;

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

    // function manipulateAllAllocated(Tiers tier) public {
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

    function checkMembership(address _memberAddress)
        public
        returns (uint256 membership)
    {
        (
            uint256 totalStaked,
            uint256 totalLockedBalance,
            uint256 freeToUnstakeBalance,
            uint256 lastBalancesUpdate,
            uint256 totalReward,
            uint256 lastRewardUpdate
        ) = stakingContract.stakeholders(_memberAddress);

        //TODO return number not int
        uint256 membership = 0;
        //TODO need to add NONE as tier as well

        // update member balances
        stakingContract.updateStakeholderBalances(_memberAddress);
        // verifies if address is eligible for membership
        //TODO weird number
        if (totalLockedBalance < rubyMinimum) {
            return membership;
        }

        for (
            uint i = 0;
            i < stakingContract.getStakingsLength(_memberAddress);
            i++
        ) {
            (
                uint256 totalStaked,
                uint256 timestamp,
                int256 stakingAmount,
                uint256 lockDuration
            ) = stakingContract.getStakingByIndex(_memberAddress, i);

            if (
                // check if staking is locked
                lockDuration >= 90 days &&
                block.timestamp - lockDuration < timestamp
            ) {
                // check if enough FTG staked for earning membership
                if (stakingAmount < rubyMinimum) {
                    //no privileges membership
                    membership = 0;
                } else if (
                    stakingAmount >= rubyMinimum && stakingAmount < sapphireMinimum
                ) {
                    //ruby membership
                    allAllocated[Tiers.RUBY] =
                        allAllocated[Tiers.RUBY] -
                        eachRubyTicket;
                    ticketAllocated[Tiers.RUBY] =
                        ticketAllocated[Tiers.RUBY] +
                        eachRubyTicket;
                    membership = membership > 1 ? membership : 1;
                } else if (
                    stakingAmount >= sapphireMinimum && stakingAmount < emeraldMinimum
                ) {
                    allAllocated[Tiers.SAPPHIRE] =
                        allAllocated[Tiers.SAPPHIRE] -
                        eachSapphireTicket;
                    ticketAllocated[Tiers.SAPPHIRE] =
                        ticketAllocated[Tiers.SAPPHIRE] +
                        eachSapphireTicket;
                    //sapphire membership
                    membership = membership > 2 ? membership : 2;
                } else if (
                    stakingAmount >= emeraldMinimum && stakingAmount < diamondMinimum
                ) {
                    allAllocated[Tiers.EMERALD] =
                        allAllocated[Tiers.EMERALD] -
                        eachEmeraldTicket;
                    ticketAllocated[Tiers.EMERALD] =
                        ticketAllocated[Tiers.EMERALD] +
                        eachEmeraldTicket;
                    //emerald membership
                    membership = 3;
                } else {
                    //diamond membership
                    allAllocated[Tiers.RUBY] =
                        allAllocated[Tiers.RUBY] -
                        eachDiamondTicket;
                    ticketAllocated[Tiers.RUBY] =
                        ticketAllocated[Tiers.RUBY] +
                        eachDiamondTicket;

                    membership = 4;
                    break;
                }
            }
        }

        return membership;
    }
}
