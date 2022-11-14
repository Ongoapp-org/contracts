// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";

import "./FTGStaking.sol";

//https://github.com/avalaunch-app/xava-protocol/blob/master/contracts/sales/AvalaunchSale.sol

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
        //uint256 amountAllocated;
    }

    enum Tiers {
        NONE,
        RUBY,
        EMERALD,
        SAPPHIRE,
        DIAMOND
    }

    string public nameSale;

    mapping(address => Participant) public participants;

    mapping(address => bool) public whitelist;
                    
    // Amount of tokens to sell
    uint256 public totalTokensToSell;
    // tokens sold so far
    uint256 public tokensSold;
    // Total ETH Raised so far
    uint256 public investRaised;
    // amount to raise in total
    uint256 public totalToRaise;
    // Sale end time
    uint256 public saleEnd;
    // Price of the token quoted in USD
    uint256 public tokenPriceInUSD;

    address stakingContractAddress;

    uint32 factor = 10_000;

    //total allocated per tier
    mapping(Tiers => uint32) public allocTotal;
    //particpants per tier
    mapping(Tiers => uint32) public tiersParticipants;
    //ticket allocated for each tier, intialized at maximum and subtracted
    mapping(Tiers => uint32) public tiersAllocated;   

    mapping(Tiers => uint32) public tiersMin;

    constructor(
        string memory _name,
        address _investToken,
        address _saleToken,
        address _stakingContractAddress,
        uint256 _tokenPriceInUSD,
        uint256 _totalTokensToSell,
        uint256 _totalToRaise
    ) {
        nameSale = _name;
        investToken = _investToken;
        saleToken = _saleToken;
        stakingContractAddress = _stakingContractAddress;
        tokenPriceInUSD = _tokenPriceInUSD;
        totalTokensToSell = _totalTokensToSell;
        totalToRaise = _totalToRaise;
        tokensSold = 0;
        investRaised = 0;
    }

    function setMins(uint32 _rubyMin, uint32 _sapphireMin, uint32 _emeraldMin, uint32 _diamondMin) public onlyOwner {
        tiersMin[Tiers.RUBY] = _rubyMin;
        tiersMin[Tiers.SAPPHIRE] = _sapphireMin;
        tiersMin[Tiers.EMERALD] = _emeraldMin;
        tiersMin[Tiers.DIAMOND] = _diamondMin;
    }

    function setAllocs(uint32 _rubyAllocTotal, uint32 _sapphireAllocTotal, uint32 _emeraldAllocTotal, uint32 _diamondAllocTotal) public onlyOwner {
        uint256 total = _rubyAllocTotal + _sapphireAllocTotal + _emeraldAllocTotal + _diamondAllocTotal;
        require(total == 100, "not 100% allocated");

        allocTotal[Tiers.RUBY] = _rubyAllocTotal;
        allocTotal[Tiers.SAPPHIRE] = _sapphireAllocTotal;
        allocTotal[Tiers.EMERALD] = _emeraldAllocTotal;
        allocTotal[Tiers.DIAMOND] = _diamondAllocTotal;
    }

    function setParticipants(uint32 _rubyP, uint32 _sapphireP, uint32 _emeraldP, uint32 _diamondP) public onlyOwner {

        tiersParticipants[Tiers.RUBY] = _rubyP;
        tiersParticipants[Tiers.SAPPHIRE] = _sapphireP;
        tiersParticipants[Tiers.EMERALD] = _emeraldP;
        tiersParticipants[Tiers.DIAMOND] = _diamondP;

        //init with maximum and count down
        tiersAllocated[Tiers.RUBY] = allocTotal[Tiers.RUBY] / tiersParticipants[Tiers.RUBY];
        tiersAllocated[Tiers.SAPPHIRE] = allocTotal[Tiers.SAPPHIRE] / tiersParticipants[Tiers.SAPPHIRE];
        tiersAllocated[Tiers.EMERALD] = allocTotal[Tiers.EMERALD] / tiersParticipants[Tiers.EMERALD];
        tiersAllocated[Tiers.DIAMOND] = allocTotal[Tiers.DIAMOND] / tiersParticipants[Tiers.DIAMOND];

    }

    // TODO dynamic if pools unused
    function amountEligible(address account) public view returns (uint256) {
        uint256 amountLocked = uint(IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(account, 30 days));
        uint256 amountElig = 0;
        //TODO percent * total
        if (amountLocked >= tiersMin[Tiers.DIAMOND]){
            amountElig = factor * allocTotal[Tiers.DIAMOND] / tiersParticipants[Tiers.DIAMOND];
        } else if (amountLocked >= tiersMin[Tiers.EMERALD]) {
            amountElig = factor * allocTotal[Tiers.EMERALD] / tiersParticipants[Tiers.EMERALD];
        } else if (amountLocked >= tiersMin[Tiers.SAPPHIRE]) {
            amountElig = factor * allocTotal[Tiers.SAPPHIRE] / tiersParticipants[Tiers.SAPPHIRE];
        } else if (amountLocked >= tiersMin[Tiers.RUBY]) {
            amountElig = factor * allocTotal[Tiers.RUBY] / tiersParticipants[Tiers.RUBY];
        } 
        return amountElig;
    }

    function _checkStaking() private {
        //calculate amount staked in 30 days or more
        //subtract amount from available pool
        //amountGuaranteedPool -= participantAmount;
    }

    function addWhitelist(address p) external onlyOwner {
        //TODO set amount?
        whitelist[p] = true;

        //TODO other steps?
    }

    //checkParticipationSignature

    //take part in the sale i.e buy tokens, pass signature on frontend
    function participate(uint256 amountTokensBuy) external {
        //TODO is tier allowed?

        require(whitelist[msg.sender], "not in whitelist");
        //determine allocation size
        uint256 amountElig = amountEligible(msg.sender);
        //TODO
        require(amountTokensBuy <= amountElig, "amount too high not eliglbe");

        // bytes calldata signature
        // signature verifies KYC

        //price is fixed

        uint256 tokenInvested = amountTokensBuy * tokenPriceInUSD/factor;
        IERC20(investToken).transferFrom(msg.sender, address(this), tokenInvested);
        IERC20(saleToken).transfer(msg.sender, amountTokensBuy);

        participants[msg.sender].amountInvested += tokenInvested;
        participants[msg.sender].tokensBought += amountTokensBuy;  

        tokensSold += amountTokensBuy;
        investRaised +=tokenInvested;

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