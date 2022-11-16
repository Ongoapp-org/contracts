// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";

import "./FTGStaking.sol";

/**
 * @title FTGSale
 * @notice This contract is deployed for every sale and specific to a given sale
 */

// TODO double check decimals
//TODO handle 2 pools
//Guaranteed Pool
//Public Pool
contract FTGSale is Ownable {
    // Token being sold
    address public saleToken;
    // invest token eg USDT
    address public investToken;

    struct Participant {
        uint256 amountInvested;
        uint256 tokensBought;
        bool whitelisted;
        //uint256 amountEligible;
    }

    enum Tiers {
        NONE,
        RUBY,
        EMERALD,
        SAPPHIRE,
        DIAMOND
    }

    string public nameSale;

    // list of participants to the sale
    mapping(address => Participant) public participants;

    // Amount of tokens to sell
    uint256 public totalTokensToSell;
    // tokens sold so far
    uint256 public tokensSold;
    // Total Raised so far
    uint256 public investRaised;
    // amount to raise in total
    uint256 public totalToRaise;
    // Sale end time
    uint256 public saleEnd;
    // Price of the token quoted in investToken
    uint256 public tokenPrice;

    address stakingContractAddress;

    // precision factor
    uint32 factor = 10_000;

    //total allocated per tier
    mapping(Tiers => uint32) public tiersTotal;
    //participants per tier
    mapping(Tiers => uint32) public tiersParticipants;
    //ticket allocated for each tier, initialized at maximum and dynamically updated
    mapping(Tiers => uint32) public tiersAllocated;
    //ftg staking threshold  for tiers
    mapping(Tiers => uint32) public tiersMin;
    //is tier active to participate
    mapping(Tiers => bool) public tiersActiveSale;

    constructor(
        string memory _name,
        address _investToken,
        address _saleToken,
        address _stakingContractAddress,
        uint256 _tokenPrice,
        uint256 _totalTokensToSell,
        uint256 _totalToRaise,
        uint256 _duration
    ) {
        nameSale = _name;
        investToken = _investToken;
        saleToken = _saleToken;
        stakingContractAddress = _stakingContractAddress;
        tokenPrice = _tokenPrice;
        totalTokensToSell = _totalTokensToSell;
        totalToRaise = _totalToRaise;
        saleEnd = block.timestamp + _duration;
        tokensSold = 0;
        investRaised = 0;
    }

    //function allows owner to set ftg staking threshold for tiers
    function setMins(
        uint32 _rubyMin,
        uint32 _sapphireMin,
        uint32 _emeraldMin,
        uint32 _diamondMin
    ) public onlyOwner {
        tiersMin[Tiers.RUBY] = _rubyMin;
        tiersMin[Tiers.SAPPHIRE] = _sapphireMin;
        tiersMin[Tiers.EMERALD] = _emeraldMin;
        tiersMin[Tiers.DIAMOND] = _diamondMin;
    }

    // set repartition of tokens for sale between Tiers
    function setAllocs(
        uint32 _rubyAllocTotal,
        uint32 _sapphireAllocTotal,
        uint32 _emeraldAllocTotal,
        uint32 _diamondAllocTotal
    ) public onlyOwner {
        uint256 total = _rubyAllocTotal +
            _sapphireAllocTotal +
            _emeraldAllocTotal +
            _diamondAllocTotal;
        require(total == 100, "not 100% allocated");

        tiersTotal[Tiers.RUBY] = _rubyAllocTotal;
        tiersTotal[Tiers.SAPPHIRE] = _sapphireAllocTotal;
        tiersTotal[Tiers.EMERALD] = _emeraldAllocTotal;
        tiersTotal[Tiers.DIAMOND] = _diamondAllocTotal;
    }

    function signupForSale() public {
        //require KYC has been done
        require(checkKYC(), "KYC requirements not fullfilled")
        Tier tier = 
        require()

    }

    //
    function setParticipants(
        uint32 _rubyP,
        uint32 _sapphireP,
        uint32 _emeraldP,
        uint32 _diamondP
    ) public onlyOwner {
        tiersParticipants[Tiers.RUBY] = _rubyP;
        tiersParticipants[Tiers.SAPPHIRE] = _sapphireP;
        tiersParticipants[Tiers.EMERALD] = _emeraldP;
        tiersParticipants[Tiers.DIAMOND] = _diamondP;

        //init with maximum and count down
        tiersAllocated[Tiers.RUBY] =
            tiersTotal[Tiers.RUBY] /
            tiersParticipants[Tiers.RUBY];
        tiersAllocated[Tiers.SAPPHIRE] =
            tiersTotal[Tiers.SAPPHIRE] /
            tiersParticipants[Tiers.SAPPHIRE];
        tiersAllocated[Tiers.EMERALD] =
            tiersTotal[Tiers.EMERALD] /
            tiersParticipants[Tiers.EMERALD];
        tiersAllocated[Tiers.DIAMOND] =
            tiersTotal[Tiers.DIAMOND] /
            tiersParticipants[Tiers.DIAMOND];
    }


 // returns the highest eligible membership (0:none, 1:ruby, 2:sapphire, 3:emerald, 4:diamond)
    function checkMembership(address _memberAddress)
        public
        returns (uint256 membership)
    {
        // update member balances
        _updateStakeholderBalances(_memberAddress);
        // verifies if address is eligible for membership
        if (stakeholders[_memberAddress].totalLockedBalance < 100_000) {
            return membership;
        }
        int256 stakingAmount;
        Staking[] memory memberStakings = stakeholders[_memberAddress].stakings;
        for (uint256 i = 0; i < memberStakings.length; i++) {
            stakingAmount = memberStakings[i].amount;
            if (
                // check if staking is locked
                memberStakings[i].lockDuration >= 90 days &&
                block.timestamp - memberStakings[i].lockDuration <
                memberStakings[i].timestamp
            ) {
                // check if enough FTG staked for earning membership
                if (stakingAmount < 100_000) {
                    //no privileges membership
                    membership = 0;
                } else if (
                    stakingAmount >= 100_000 && stakingAmount < 250_000
                ) {
                    //ruby membership
                    membership = membership > 1 ? membership : 1;
                } else if (
                    stakingAmount >= 250_000 && stakingAmount < 500_000
                ) {
                    //sapphire membership
                    membership = membership > 2 ? membership : 2;
                } else if (
                    stakingAmount >= 500_000 && stakingAmount < 1_000_000
                ) {
                    //emerald membership
                    membership = 3;
                } else {
                    //diamond membership
                    membership = 4;
                    break;
                }
            }
        }
        return membership;
    }






    // TODO dynamic if pools unused
    function amountEligible(address account) public view returns (uint256) {
        uint256 amountLocked = uint256(
            IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(
                account,
                30 days
            )
        );

        // check if enough FTG staked for earning membership
                if (stakingAmount < 100_000) {
                    //no privileges membership
                    membership = 0;
                } else if (
                    stakingAmount >= 100_000 && stakingAmount < 250_000
                ) {
                    //ruby membership
                    membership = membership > 1 ? membership : 1;
                } else if (
                    stakingAmount >= 250_000 && stakingAmount < 500_000
                ) {
                    //sapphire membership
                    membership = membership > 2 ? membership : 2;
                } else if (
                    stakingAmount >= 500_000 && stakingAmount < 1_000_000
                ) {
                    //emerald membership
                    membership = 3;
                } else {
                    //diamond membership
                    membership = 4;
                    break;
                }
            }
        }
        return membership;



        uint256 amountElig = 0;
        //TODO percent * total
        if (amountLocked >= tiersMin[Tiers.DIAMOND]) {
            amountElig =
                (factor * tiersTotal[Tiers.DIAMOND]) /
                tiersParticipants[Tiers.DIAMOND];
        } else if (amountLocked >= tiersMin[Tiers.EMERALD]) {
            amountElig =
                (factor * tiersTotal[Tiers.EMERALD]) /
                tiersParticipants[Tiers.EMERALD];
        } else if (amountLocked >= tiersMin[Tiers.SAPPHIRE]) {
            amountElig =
                (factor * tiersTotal[Tiers.SAPPHIRE]) /
                tiersParticipants[Tiers.SAPPHIRE];
        } else if (amountLocked >= tiersMin[Tiers.RUBY]) {
            amountElig =
                (factor * tiersTotal[Tiers.RUBY]) /
                tiersParticipants[Tiers.RUBY];
        }
        return amountElig;
    }

    function addWhitelist(address p) external onlyOwner {
        participants[p].whitelisted = true;

        //add eligble now?
    }

    //checkParticipationSignature

    //take part in the sale i.e buy tokens, pass signature on frontend
    function participate(uint256 amountTokensBuy) external {
        //TODO is tier allowed?

        require(participants[msg.sender].whitelisted, "not in whitelist");
        require(block.timestamp < saleEnd, "sale ended");

        //determine allocation size
        uint256 amountElig = amountEligible(msg.sender);
        //TODO
        require(amountTokensBuy <= amountElig, "amount too high not eliglbe");

        // bytes calldata signature
        // signature verifies KYC

        //price is fixed

        uint256 tokenInvested = (amountTokensBuy * tokenPrice) / factor;
        IERC20(investToken).transferFrom(
            msg.sender,
            address(this),
            tokenInvested
        );
        IERC20(saleToken).transfer(msg.sender, amountTokensBuy);

        participants[msg.sender].amountInvested += tokenInvested;
        participants[msg.sender].tokensBought += amountTokensBuy;

        tokensSold += amountTokensBuy;
        investRaised += tokenInvested;
    }

    // Function for owner to deposit tokens
    function depositSaleTokens(uint256 amount) public onlyOwner {
        IERC20(saleToken).transferFrom(msg.sender, address(this), amount);
    }

    function withdrawLeftOverTokens() public onlyOwner {
        uint256 bal = IERC20(saleToken).balanceOf(address(this));
        IERC20(saleToken).transfer(msg.sender, bal);
    }

    function withdrawRaisedAssets() public onlyOwner {
        uint256 bal = IERC20(investToken).balanceOf(address(this));
        IERC20(saleToken).transfer(msg.sender, bal);
    }
}
