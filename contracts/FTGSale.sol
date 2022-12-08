// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";
import "./FTGStaking.sol";
import "./NRT.sol";

/**
 * @title FTGSale
 * @notice This contract is deployed for every sale and specific to a given sale
 */

//Guaranteed Pool
//Public Pool
contract FTGSale is Ownable {
    //tiers Memberships
    enum Tiers {
        NONE,
        RUBY,
        EMERALD,
        SAPPHIRE,
        DIAMOND
    }

    //Sale Phases
    enum Phases {
        Setup,
        Registration,
        GuaranteedPool,
        PublicPool,
        SaleCompleted
    }

    struct Participant {
        uint256 tokensBalanceGP;
        uint256 tokensBalancePP;
        bool whitelisted;
        Tiers participantTier;
    }

    Phases public salePhase;

    // Phases durations
    uint256 registrationPhaseDuration;
    uint256 guaranteedPoolPhaseDuration;
    uint256 publicPoolPhaseDuration;
    // token being sold
    //address immutable saleToken;
    // invest token eg USDT
    address immutable investToken;
    // staking contract
    address immutable stakingContractAddress;
    // price of the token quoted in investToken (wei)
    uint256 immutable tokenPriceWei;
    // amount of tokens to sell
    uint256 immutable totalTokensToSell;
    // amount to raise in total
    uint256 immutable totalToRaise;
    // sale starts with registration
    uint256 public registrationPhaseStart;
    uint256 public guaranteedPoolPhaseStart;
    uint256 public publicPoolPhaseStart;

    // tokens sold so far
    uint256 public tokensSold;
    // total Raised so far
    uint256 public investmentRaised;
    // precision Factor
    uint256 constant precisionFactor = 1_000_000_000;
    // ruby tier max number of tokens per participant
    uint256 public n;
    // nb of participants
    uint256 public np;
    // max number purchaseable
    uint256 public n2;
    // tokens to sell during public sale, remaining
    uint256 publicSaleTokens;

    NRT public nrt;

    // list of participants to the sale
    mapping(address => Participant) public participants;
    //TODO
    mapping(Tiers => uint32) public tiersTokensAllocationFactor;
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
        address _nrt,
        address _investToken,
        address _stakingContractAddress,
        uint256 _tokenPriceWei, // fix price for entire sale ?
        uint256 _totalTokensToSell,
        uint256 _totalToRaise
    ) {
        investToken = _investToken;
        //saleToken = _saleToken;
        nrt = NRT(_nrt);
        stakingContractAddress = _stakingContractAddress;
        tokenPriceWei = _tokenPriceWei;
        totalTokensToSell = _totalTokensToSell;
        totalToRaise = _totalToRaise;
        tokensSold = 0;
        investmentRaised = 0;
        salePhase = Phases.Setup;
    }

    //function to go to next phase
    function launchNextPhase() public onlyOwner {
        if (salePhase == Phases.Setup) {
            //requirement setTiersMinFTGStakings is valid , should it really be setup here?
            //requirement setTokenAllocation is valid ?
            registrationPhaseStart = block.timestamp;
            salePhase = Phases.Registration;
        } else if (salePhase == Phases.Registration) {
            //once the registration time is finished
            //calculate the max number of tokens for sale by participants
            _guaranteedSalePreliminaryCalculation();
            guaranteedPoolPhaseStart = block.timestamp;
            salePhase = Phases.GuaranteedPool;
        } else if (salePhase == Phases.GuaranteedPool) {
            _publicSalePreliminaryCalculation();
            publicPoolPhaseStart = block.timestamp;
            salePhase = Phases.PublicPool;
        } else if (salePhase == Phases.PublicPool) {
            //owner launch this phase to open tokens claim by participants
            salePhase = Phases.SaleCompleted;
        } else {
            revert();
        }
    }

    //********************* Setup Phase functions *********************/

    // set phases durations
    function setPhasesDurations(
        uint256 _registrationPhaseDuration,
        uint256 _guaranteedPoolPhaseDuration,
        uint256 _publicPoolPhaseDuration
    ) public onlyOwner {
        registrationPhaseDuration = _registrationPhaseDuration;
        guaranteedPoolPhaseDuration = _guaranteedPoolPhaseDuration;
        publicPoolPhaseDuration = _publicPoolPhaseDuration;
    }

    // function allows owner to set tiers min ftg staking threshold
    // should it really be setup here? does it vary between sales?
    function setTiersMinFTGStakings(
        uint32 _rubyMin,
        uint32 _emeraldMin,
        uint32 _sapphireMin,
        uint32 _diamondMin
    ) public onlyOwner {
        tiersMinFTGStaking[Tiers.RUBY] = _rubyMin;
        tiersMinFTGStaking[Tiers.EMERALD] = _emeraldMin;
        tiersMinFTGStaking[Tiers.SAPPHIRE] = _sapphireMin;
        tiersMinFTGStaking[Tiers.DIAMOND] = _diamondMin;
    }

    // set tiers tokens allocation
    function setTiersTokensAllocationFactors(
        uint32 _sapphireAllocationFactor,
        uint32 _emeraldAllocationFactor,
        uint32 _diamondAllocationFactor
    ) public onlyOwner {
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

    //********************* Registration Phase functions *********************/

    function registerForSale() public {
        require(salePhase == Phases.Registration, "Registration not open");
        require(
            block.timestamp <
                registrationPhaseStart + registrationPhaseDuration,
            "Registration Phase ended"
        );
        // requirement that KYC has been done in the frontend
        // requirement that caller is eligible
        Tiers tier = checkTierEligibility(msg.sender);
        require(tier != Tiers.NONE, "Not enough locked Staking");
        // add participant and set whitelist to true
        participants[msg.sender] = Participant(0, 0, true, tier);
        // add participant to tiersNbOFParticipants
        tiersNbOFParticipants[tier]++;
    }

    function checkTierEligibility(address account) public view returns (Tiers) {
        // check active locked staking for account
        uint256 activeStakingLocked = uint256(
            IFTGStaking(stakingContractAddress).checkParticipantLockedStaking(
                account,
                30 days
            )
        );
        // check eligible tier earned
        if (activeStakingLocked < tiersMinFTGStaking[Tiers.RUBY]) {
            //if (activeStakingLocked < tiersMinFTGStaking[0]) {
            //no privileges membership
            return Tiers.NONE;
        } else if (
            activeStakingLocked >= tiersMinFTGStaking[Tiers.RUBY] &&
            activeStakingLocked < tiersMinFTGStaking[Tiers.SAPPHIRE]
        ) {
            //ruby membership
            return Tiers.RUBY;
        } else if (
            activeStakingLocked >= tiersMinFTGStaking[Tiers.SAPPHIRE] &&
            activeStakingLocked < tiersMinFTGStaking[Tiers.EMERALD]
        ) {
            //sapphire membership
            return Tiers.SAPPHIRE;
        } else if (
            activeStakingLocked >= tiersMinFTGStaking[Tiers.EMERALD] &&
            activeStakingLocked < tiersMinFTGStaking[Tiers.DIAMOND]
        ) {
            //emerald membership
            return Tiers.EMERALD;
        } else {
            //TODO double check
            //diamond membership
            return Tiers.DIAMOND;
        }
    }

    //********************* Sale Phases functions *********************/

    //this function to calculate n the max number of tokens for sale by participant in Ruby Tier
    function _guaranteedSalePreliminaryCalculation() private {
        //require registration phase is over
        require(
            registrationPhaseStart != 0 &&
                block.timestamp >
                registrationPhaseStart + registrationPhaseDuration,
            "registration not finished"
        );
        //NP = number of participants
        //Factor * NP
        uint256 sumFNP = tiersTokensAllocationFactor[Tiers.SAPPHIRE] *
            tiersNbOFParticipants[Tiers.SAPPHIRE] +
            tiersTokensAllocationFactor[Tiers.EMERALD] *
            tiersNbOFParticipants[Tiers.EMERALD] +
            tiersTokensAllocationFactor[Tiers.DIAMOND] *
            tiersNbOFParticipants[Tiers.DIAMOND] +
            tiersNbOFParticipants[Tiers.RUBY];
        //n = max number of tokens that ruby participant can buy
        n = PRBMath.mulDiv(
            precisionFactor, // multiplier for calculation precision
            totalTokensToSell,
            sumFNP
        );
    }

    //calculation for public phase
    function _publicSalePreliminaryCalculation() private {
        //require registration phase is over
        require(
            guaranteedPoolPhaseStart != 0 &&
                block.timestamp >
                guaranteedPoolPhaseStart + guaranteedPoolPhaseDuration,
            "guaranteedPool Sale not finished"
        );
        //np = number of participants calculated
        np =
            tiersNbOFParticipants[Tiers.RUBY] +
            tiersNbOFParticipants[Tiers.SAPPHIRE] +
            tiersNbOFParticipants[Tiers.EMERALD] +
            tiersNbOFParticipants[Tiers.DIAMOND];
        //remaining
        publicSaleTokens = totalTokensToSell - tokensSold;
        //n2 = max tokens someone can buy regardless the tier
        n2 = PRBMath.mulDiv(
            precisionFactor, // multiplier for calculation precision
            publicSaleTokens,
            np
        );
    }

    //function to buy tokens during Pool Phases
    //TODO change to investToken
    function buytoken(uint256 buyTokenAmount) public {
        //verifies that participants has been KYCed
        require(participants[msg.sender].whitelisted, "not in whitelist");
        Tiers tier = participants[msg.sender].participantTier;
        require(
            salePhase == Phases.GuaranteedPool ||
                salePhase == Phases.PublicPool,
            "not open for buying"
        );
        if (salePhase == Phases.GuaranteedPool) {
            //Verifies that phase is not over
            require(
                block.timestamp <
                    guaranteedPoolPhaseStart + guaranteedPoolPhaseDuration,
                "Guaranteed Pool Phase ended"
            );
            //require participant is buying less than entitled to
            require(
                participants[msg.sender].tokensBalanceGP + buyTokenAmount <
                    n * tiersTokensAllocationFactor[tier],
                "your tokensBalance would exceed the maximum allowed number of tokens"
            );
            //TODO double check precision
            uint256 investedAmount = (buyTokenAmount * tokenPriceWei) / 10**18;
            //purchase takes place
            IERC20(investToken).transferFrom(
                msg.sender,
                address(this),
                investedAmount
            );
            // balances are updated
            tokensSold += buyTokenAmount;
            investmentRaised += investedAmount;
            participants[msg.sender].tokensBalanceGP += buyTokenAmount;
            nrt.issue(msg.sender, buyTokenAmount);
            if (investmentRaised >= totalToRaise) {
                // Sale is completed and participants can claim their tokens
                salePhase = Phases.SaleCompleted;
            }
        } else if (salePhase == Phases.PublicPool) {
            //verifies that phase is not over
            require(
                block.timestamp <
                    publicPoolPhaseStart + publicPoolPhaseDuration,
                "Public Pool Phase ended"
            );
            //require participant is buying less than entitled to

            //TODO double check
            require(
                participants[msg.sender].tokensBalancePP + buyTokenAmount < n2,
                "your tokensBalance would exceed the maximum allowed number of tokens"
            );
            uint256 investedAmount = (buyTokenAmount * tokenPriceWei) / 10**18;
            //purchase takes place
            IERC20(investToken).transferFrom(
                msg.sender,
                address(this),
                investedAmount
            );
            // balances are updated
            investmentRaised += investedAmount;
            participants[msg.sender].tokensBalancePP += buyTokenAmount;
            nrt.issue(msg.sender, buyTokenAmount);

            if (investmentRaised >= totalToRaise) {
                // Sale is completed and participants can claim their tokens
                salePhase = Phases.SaleCompleted;
            }
        }
    }

    function withdrawRaisedAssets() public onlyOwner {
        uint256 bal = IERC20(investToken).balanceOf(address(this));
        IERC20(investToken).transfer(msg.sender, bal);
    }

    function recoverAssets(address _token) public onlyOwner {
        uint256 bal = IERC20(_token).balanceOf(address(this));
        IERC20(_token).transfer(msg.sender, bal);
    }
}
