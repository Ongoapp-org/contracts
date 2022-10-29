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

    string nameSale;

    mapping(address => Participant) public participants;

    mapping(address => bool) public whitelist; 

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

    //TODO
    uint256 amountGuaranteedPool = 1_000_000;
    uint256 amountPublicPool = 500_000;

    constructor(string _name, address _stakingContractAddress, uint _amountGuaranteedPool, uint256 _tokenPriceInUSD) {
        nameSale = _name;
        stakingContract = FTGStaking(_stakingContractAddress);
        amountGuaranteedPool = _amountGuaranteedPool;
        tokenPriceInUSD = _tokenPriceInUSD;
    }

    //determine which level
    function checkMembership() {

        //TODO calculate score potentially
        //TODO maybe need to loop through 
        //calculate lock at least 30days
        //uint256 amountStaked = stakingContract.stakeholders[msg.sender].stakings;
        uint256 amountStaked = stakingContract.totalFTGStaked;
        if (amountStaked > diamondMinimum){
            //TODO calcualte total available in guarnateed pool and subtract??
            uint256 participantAmount = 100;
            participants[msg.sender] = Participant(msg.sender, participantAmount);

            
        } else if (amountStaked > emeraldMinimum){

        }

    }

    // TODO calculate amount eligible
    function amountEligible() {

    }

    function checkStaking() {
        //calculate amount staked in 30 days or more

        //subtract amount from available pool
        //amountGuaranteedPool -= participantAmount;
        
    }

    function addWhitelist(address p) onlyOwner {
        whitelist[p] = true;

        //TODO other steps?
    }


    //checkParticipationSignature


    //take part in the sale i.e buy tokens, pass signature on frontend
    function participate(uint256 amountTokensBuy) {
        //TODO which pool

        require(whitelist[msg.sender], "not in whitelist");
        //determine allocation size
        uint256 amountElig = amountEligible(msg.sender);
        require(amountTokensBuy <= amountElig, "amount too high not eliglbe");

        // bytes calldata signature
        // signature verifies KYC

        //price is fixed

        uint256 costInUSD = amountTokensBuy * tokenPriceInUSD;
        IERC20(investToken).transferFrom(costInUSD, address(this));

        IERC20(saleToken).transfer(msg.sender, amountTokensBuy);


    }

    // Function for owner to deposit tokens
    //function depositTokens() onlyOwner {}

    //TODO
    //function withdrawLeftOverTokens() onlyOwner {}

    //TODO
    //function withdrawRaisedAssets() onlyOwner {}

}