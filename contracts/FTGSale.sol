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

    enum Phase {
        Registration,
        GuarantedPool,
        PublicPool,
        SaleCompleted
    }

    Phase salePhase;

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
    mapping(Tiers => uint32) public tiersNbOFParticipants;
    //ticket allocated for each tier, initialized at maximum and dynamically updated
    mapping(Tiers => uint32) public tiersAllocated;
    //ftg staking threshold  for tiers
    mapping(Tiers => uint32) public tiersMinFTGStaking;
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
        tiersMinFTGStaking[Tiers.RUBY] = _rubyMin;
        tiersMinFTGStaking[Tiers.SAPPHIRE] = _sapphireMin;
        tiersMinFTGStaking[Tiers.EMERALD] = _emeraldMin;
        tiersMinFTGStaking[Tiers.DIAMOND] = _diamondMin;
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
        //requirement that we are in the Registration Phase
        require(phase == Phase.Registration, "Registration not open");
        //requirement that KYC has been done
        require(checkKYC(msg.sender), "KYC requirements not fullfilled");
        //requirement that caller is eligible
        Tiers tier = checkTierEligibility(msg.sender);
        require(tier != Tiers.NONE, "Not enough locked Staking");
        // add participant
        participants[msg.sender] = participant(0, 0, true);
        // add participant to tiersNbOfParticipants
        tiersNbOfParticipants[tier]++;
    }

    //
    function tiersMaxTokenAmount(
        uint32 _rubyP,
        uint32 _sapphireP,
        uint32 _emeraldP,
        uint32 _diamondP
    ) public onlyOwner {
        tiersNbOfParticipants[Tiers.RUBY] = _rubyP;
        tiersNbOfParticipants[Tiers.SAPPHIRE] = _sapphireP;
        tiersNbOfParticipants[Tiers.EMERALD] = _emeraldP;
        tiersNbOfParticipants[Tiers.DIAMOND] = _diamondP;

        //init with maximum and count down
        tiersAllocated[Tiers.RUBY] =
            tiersTotal[Tiers.RUBY] /
            tiersNbOfParticipants[Tiers.RUBY];
        tiersAllocated[Tiers.SAPPHIRE] =
            tiersTotal[Tiers.SAPPHIRE] /
            tiersNbOfParticipants[Tiers.SAPPHIRE];
        tiersAllocated[Tiers.EMERALD] =
            tiersTotal[Tiers.EMERALD] /
            tiersNbOfParticipants[Tiers.EMERALD];
        tiersAllocated[Tiers.DIAMOND] =
            tiersTotal[Tiers.DIAMOND] /
            tiersNbOfParticipants[Tiers.DIAMOND];
    }

    // TODO dynamic if pools unused
    function checkTierEligibility(address account) public view returns (Tier) {
        // check active locked staking for account
        uint256 activeStakingLocked = uint256(
            IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(
                account,
                30 days
            )
        );
        // check eligible tier earned
        if (activeStakingLocked < tiersMinFTGStaking[0]) {
            //no privileges membership
            return Tiers.NONE;
        } else if (
            activeStakingLocked >= tiersMinFTGStaking[0] &&
            activeStakingLocked < tiersMinFTGStaking[1]
        ) {
            //ruby membership
            return Tiers.RUBY;
        } else if (
            activeStakingLocked >= tiersMinFTGStaking[1] &&
            activeStakingLocked < tiersMinFTGStaking[2]
        ) {
            //sapphire membership
            return Tiers.SAPPHIRE;
        } else if (
            activeStakingLocked >= tiersMinFTGStaking[2] &&
            activeStakingLocked < tiersMinFTGStaking[3]
        ) {
            //emerald membership
            return Tiers.EMERALD;
        } else {
            //diamond membership
            return DIAMOND;
        }
    }

    /* uint256 amountElig = 0;
        //TODO percent * total
        if (amountLocked >= tiersMin[Tiers.DIAMOND]) {
            amountElig =
                (factor * tiersTotal[Tiers.DIAMOND]) /
                tiersNbOfParticipants[Tiers.DIAMOND];
        } else if (amountLocked >= tiersMin[Tiers.EMERALD]) {
            amountElig =
                (factor * tiersTotal[Tiers.EMERALD]) /
                tiersNbOfParticipants[Tiers.EMERALD];
        } else if (amountLocked >= tiersMin[Tiers.SAPPHIRE]) {
            amountElig =
                (factor * tiersTotal[Tiers.SAPPHIRE]) /
                tiersNbOfParticipants[Tiers.SAPPHIRE];
        } else if (amountLocked >= tiersMin[Tiers.RUBY]) {
            amountElig =
                (factor * tiersTotal[Tiers.RUBY]) /
                tiersNbOfParticipants[Tiers.RUBY];
        }
        return amountElig;
    } */

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
