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
    struct Participant {
        uint256 amountInvested;
        uint256 tokensBought;
        bool whitelisted;
        tier participantTier;
    }

    //Sale Phases
    enum Phases {
        Setup,
        Registration,
        GuaranteedPool,
        PublicPool,
        SaleCompleted
    }
    Phases salePhase;

    //tiers Memberships
    enum Tiers {
        NONE,
        RUBY,
        EMERALD,
        SAPPHIRE,
        DIAMOND
    }

    // tokens sale's name
    string public saleName;
    // Phases durations
    uint256 immutable registrationPhaseDuration;
    uint256 immutable garanteedPoolPhaseDuration;
    uint256 immutable publicPoolPhaseDuration;
    // token being sold
    address immutable saleToken;
    // invest token eg USDT
    address immutable investToken;
    // staking contract
    address immutable stakingContractAddress;
    // price of the token quoted in investToken
    uint256 immutable tokenPrice;
    // amount of tokens to sell
    uint256 immutable totalTokensToSell;
    // amount to raise in total ?? Should we end the sale when it is reached?
    uint256 immutable totalToRaise;
    // sale starts with registration ...
    uint256 public registrationPhaseStart;
    uint256 public guaranteedPoolPhaseStart;
    uint256 public publicPoolPhaseStart;
    // tokens sold so far
    uint256 public tokensSold;
    // total Raised so far
    uint256 public investmentRaised;
    // precision factor
    uint32 constant factor = 10_000;

    // list of participants to the sale
    mapping(address => Participant) public participants;
    // total allocated tokens per tier
    mapping(Tiers => uint32) public tiersTotalTokenAllocation;
    // number of participants per tier
    mapping(Tiers => uint32) public tiersNbOFParticipants;
    // ticket allocated for each tier, initialized at maximum and dynamically updated
    mapping(Tiers => uint32) public tiersMaxTokensForSalePerParticipant;
    // ftg staking threshold  for tiers
    mapping(Tiers => uint32) public tiersMinFTGStaking;
    // is tier active to participate ??? Probably not needed
    mapping(Tiers => bool) public tiersActiveSale;

    //Owner deploy contract and launches sale at the same time
    constructor(
        string memory _name,
        uint256 _registrationPhaseDuration,
        uint256 _guaranteedPoolPhaseDuration,
        uint256 _publicPoolPhaseDuration,
        address _saleToken,
        address _investToken,
        address _stakingContractAddress,
        uint256 _tokenPrice, // fix price for entire sale ?
        uint256 _totalTokensToSell,
        uint256 _totalToRaise,
        uint32 _rubyMin,
        uint32 _sapphireMin,
        uint32 _emeraldMin,
        uint32 _diamondMin
    ) {
        saleName = _name;
        registrationPhaseDuration = _registrationPhaseDuration;
        guaranteedPoolPhaseDuration = _guaranteedPoolPhaseDuration;
        publicPoolPhaseDuration = _publicPoolPhaseDuration;
        investToken = _investToken;
        saleToken = _saleToken;
        stakingContractAddress = _stakingContractAddress;
        tokenPrice = _tokenPrice;
        totalTokensToSell = _totalTokensToSell;
        totalToRaise = _totalToRaise;
        tokensSold = 0;
        investmentRaised = 0;
        phase = Phases.Setup;
    }

    //function to go to next phase
    function launchNextPhase() public onlyOwner {
        if (phase == Phases.Setup) {
            //requirement setTiersMinFTGStakings is valid , should it really be setup here?
            //requirement setTokenAllocation is valid ?
            registrationPhaseStart = block.timestamp;
            phase = Phases.Registration;
        } else if (phase == Phases.Registration) {
            guaranteedPoolPhaseStart = block.timestamp;
            phase = Phases.GuaranteedPool;
        } else if (phase == Phases.GuaranteedPool) {
            publicPoolPhaseStart = block.timestamp;
            phase = Phases.PublicPool;
        } else if (phase == Phases.PublicPool) {
            phase = Phases.SaleCompleted;
        } else {
            revert();
        }
    }

    //*********************Setup Phase functions*********************/

    //function allows owner to set tiers min ftg staking threshold
    //should it really be setup here? does it vary between sales?
    function setTiersMinFTGStakings(
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

    // set tiers tokens allocation
    function setTiersTotalTokensAllocations(
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
        tiersTotalTokenAllocation[Tiers.RUBY] = _rubyAllocTotal;
        tiersTotalTokenAllocation[Tiers.SAPPHIRE] = _sapphireAllocTotal;
        tiersTotalTokenAllocation[Tiers.EMERALD] = _emeraldAllocTotal;
        tiersTotalTokenAllocation[Tiers.DIAMOND] = _diamondAllocTotal;
    }

    //*********************Registration Phase functions*********************/

    function registerForSale() public {
        require(phase == Phases.Registration, "Registration not open");
        require(
            block.timestamp <
                registrationPhaseStart + registrationPhaseDuration,
            "Registration Phase ended"
        );
        //requirement that KYC has been done in the frontend
        //requirement that caller is eligible
        Tiers tier = checkTierEligibility(msg.sender);
        require(tier != Tiers.NONE, "Not enough locked Staking");
        // add participant
        participants[msg.sender] = participant(0, 0, true, tier);
        // add participant to tiersNbOfParticipants
        tiersNbOfParticipants[tier]++;
    }

    //this function to calculate the max purchasable number of tokens by participant in each Tier
    //need to use math function to calculate division !!!!!!
    function calculateTiersMaxTokenAmountForSalePerParticipant()
        public
        onlyOwner
    {
        if (tiersNbOfParticipants[Tiers.RUBY] != 0) {
            tiersMaxTokensForSalePerParticipant[Tiers.RUBY] =
                tiersTotalTokenAllocation[Tiers.RUBY] /
                tiersNbOfParticipants[Tiers.RUBY];
        } else {
            tiersMaxTokensForSalePerParticipant[Tiers.RUBY] = 0;
        }

        if (tiersNbOfParticipants[Tiers.SAPPHIRE] != 0) {
            tiersMaxTokensForSalePerParticipant[Tiers.SAPPHIRE] =
                tiersTotalTokenAllocation[Tiers.SAPPHIRE] /
                tiersNbOfParticipants[Tiers.SAPPHIRE];
        } else {
            tiersMaxTokensForSalePerParticipant[Tiers.SAPPHIRE] = 0;
        }

        if (tiersNbOfParticipants[Tiers.EMERALD] != 0) {
            tiersMaxTokensForSalePerParticipant[Tiers.EMERALD] =
                tiersTotalTokenAllocation[Tiers.EMERALD] /
                tiersNbOfParticipants[Tiers.EMERALD];
        } else {
            tiersMaxTokensForSalePerParticipant[Tiers.EMERALD] = 0;
        }

        if (tiersNbOfParticipants[Tiers.DIAMOND] != 0) {
            tiersMaxTokensForSalePerParticipant[Tiers.DIAMOND] =
                tiersTotalTokenAllocation[Tiers.DIAMOND] /
                tiersNbOfParticipants[Tiers.DIAMOND];
        } else {
            tiersMaxTokensForSalePerParticipant[Tiers.DIAMOND] = 0;
        }
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

    function addWhitelist(address p) external onlyOwner {
        participants[p].whitelisted = true;

        //add eligble now?
    }

    //checkParticipationSignature

    //*********************Sale Phases functions*********************/

    //function to buy tokens during Pool Phases
    function buytoken(uint256 tokensAmount) external {
        //verifies that participants has been KYCed
        require(participants[msg.sender].whitelisted, "not in whitelist");
        require(investmentRaised + tokensAmount <= totalToRaise, "max raised reached");
        if (phase == Phases.GuaranteedPool) {
            //verifies that phase is not over
            require(
                block.timestamp <
                    guaranteedPoolPhaseStart + guaranteedPoolPhaseDuration,
                "Guaranteed Pool Phase ended"
            );
            //verifies that participant has DIAMOND or EMERALD Membership
            if (
                participants[msg.sender].tier == Tiers.DIAMOND ||
                participants[msg.sender].tier == Tiers.EMERALD
            ) {}
        } else if (phase == Phases.PublicPool) {
            //verifies that phase is not over
            require(
                block.timestamp <
                    publicPoolPhaseStart + publicPoolPhaseDuration,
                "Public Pool Phase ended"
            );
        } else {
            revert("sales not open");
        }

        //??
        require(block.timestamp < 0, "sale ended");

        //determine allocation size
        uint256 amountElig = amountEligible(msg.sender);
        //TODO
        require(tokensAmount <= amountElig, "amount too high not eliglbe");

        // bytes calldata signature
        // signature verifies KYC

        //price is fixed

        uint256 tokenInvested = (tokensAmount * tokenPrice) / factor;
        IERC20(investToken).transferFrom(
            msg.sender,
            address(this),
            tokenInvested
        );
        IERC20(saleToken).transfer(msg.sender, tokensAmount);

        participants[msg.sender].amountInvested += tokenInvested;
        participants[msg.sender].tokensBought += tokensAmount;

        tokensSold += tokensAmount;
        investmentRaised += tokenInvested;
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
