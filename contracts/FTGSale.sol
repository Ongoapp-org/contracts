// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "paulrberg/prb-math@2.5.0/contracts/PRBMath.sol";
import "./FTGStaking.sol";
import "./NTT.sol";

/**
 * @title FTGSale
 * @notice This contract is deployed for every sale and specific to a given sale. The sale takes place
 * in 5 phases. The setup phase is reserved to the admin setting up the sale (duration, tiers eligibility,
 * tiers priviledges). Then the registration phase is launched by the admin for a certain duration. Participants need
 * to be kyced first, then they will be able to register before the end of the registration phase. Once registration
 * phase has ended, admin can launch the guaranteed pool phase, during which participants can acquire tokens
 * within the limit of the number of purchasable tokens per participant. This limit is depending on the tiers
 * and calculated to guarantee that higher Tiers have the possibility to purchase larger number of tokens than lower
 * Tiers. Once this guaranted pool sale period has ended, if there are remaining tokens, they are to be sold in
 * public pool sale which starts with an equal maximum number of purchasable tokens per participant regardless their tier.
 * This max number of purchasable tokens per participant is time-dependent and increases linearly till 75% of the
 * public pool sale has elapsed, at which point the number of tokens purchasable by participant is only lmited by
 * the remaining number of tokens for sale. When the sale ends, participants are free to claim their tokens.
 */

contract FTGSale is Ownable {
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
        Registration,
        GuaranteedPool,
        PublicPool,
        SaleCompleted
    }

    Phases public salePhase;

    struct Participant {
        uint256 tokensBalanceGP;
        uint256 tokensBalancePP;
        bool whitelisted;
        Tiers participantTier;
    }

    // Phases durations
    uint256 public registrationPhaseDuration;
    uint256 public guaranteedPoolPhaseDuration;
    uint256 public publicPoolPhaseDuration;
    // token being sold
    //address immutable saleToken;
    // invest token eg USDT
    address immutable investToken;
    // staking contract
    address immutable stakingContractAddress;
    // price of the token (= price of 10**18 "tokenWei") quoted in investToken
    uint256 public immutable tokenPrice;
    // amount of tokens to sell (in tokenWei)
    uint256 public immutable totalTokensToSell;
    // amount to raise in total
    uint256 public immutable totalToRaise;

    // sale starts with registration
    uint256 public registrationPhaseStart;
    uint256 public guaranteedPoolPhaseStart;
    uint256 public publicPoolPhaseStart;

    // tokens sold so far (in tokenWei)
    uint256 public tokensSold;
    // total Raised so far
    uint256 public investmentRaised;
    // ruby tier max number of tokens per participant during Guaranteed Pool
    uint256 public maxNbTokensPerPartRuby;
    // number of participants
    uint256 public NbOfParticipants;
    // max number of token purchaseable at the start of Public Pool
    uint256 public maxNbTokensPerPartAtPPStart;
    // tokens to sell at start of public sale, which were not sold in Guaranteed Pool
    uint256 public publicPoolTokensAtPPStart;

    NTT public ntt;

    // list of participants to the sale
    mapping(address => Participant) public participants;
    // factors determining Tiers relative tokens allocation in gauaranteed sale
    mapping(Tiers => uint256) public tiersTokensAllocationFactor;
    // number of participants per tier
    mapping(Tiers => uint256) public tiersNbOFParticipants;
    // ftg staking threshold  for tiers
    mapping(Tiers => uint256) public tiersMinFTGStaking;

    //events
    event newParticipant(address _participantAddress, Tiers _participantTier);
    event newPhase(Phases _newPhase);
    event newPurchase(
        address _participantAddress,
        uint256 _amount,
        Phases _salePhase
    );

    //Owner deploy contract and launches sale at the same time
    constructor(
        address _ntt,
        address _investToken,
        address _stakingContractAddress,
        uint256 _tokenPrice, // fix price for entire sale ?
        uint256 _totalTokensToSell,
        uint256 _totalToRaise
    ) {
        investToken = _investToken;
        ntt = NTT(_ntt);
        stakingContractAddress = _stakingContractAddress;
        tokenPrice = _tokenPrice;
        totalTokensToSell = _totalTokensToSell;
        totalToRaise = _totalToRaise;
        salePhase = Phases.Setup;
    }

    //function to go to next phase
    function launchNextPhase() public onlyOwner {
        if (salePhase == Phases.Setup) {
            //verif that setup was done
            require(
                registrationPhaseDuration != 0 &&
                    guaranteedPoolPhaseDuration != 0 &&
                    publicPoolPhaseDuration != 0,
                "Please setup Phases Durations"
            );
            require(
                tiersMinFTGStaking[Tiers.SAPPHIRE] != 0 &&
                    tiersMinFTGStaking[Tiers.EMERALD] != 0 &&
                    tiersMinFTGStaking[Tiers.DIAMOND] != 0,
                "Please setup tiersMinFTGStaking"
            );
            require(
                tiersTokensAllocationFactor[Tiers.SAPPHIRE] > 1 &&
                    tiersTokensAllocationFactor[Tiers.EMERALD] > 1 &&
                    tiersTokensAllocationFactor[Tiers.DIAMOND] > 1,
                "Please setup  tiersTokensAllocationFactor"
            );
            registrationPhaseStart = block.timestamp;
            salePhase = Phases.Registration;
            emit newPhase(Phases.Registration);
        } else if (salePhase == Phases.Registration) {
            //once the registration time is finished
            //calculate the max number of tokens for sale by participants
            _guaranteedSalePreliminaryCalculation();
            guaranteedPoolPhaseStart = block.timestamp;
            salePhase = Phases.GuaranteedPool;
            emit newPhase(Phases.GuaranteedPool);
        } else if (salePhase == Phases.GuaranteedPool) {
            _publicSalePreliminaryCalculation();
            publicPoolPhaseStart = block.timestamp;
            salePhase = Phases.PublicPool;
            emit newPhase(Phases.PublicPool);
        } else if (salePhase == Phases.PublicPool) {
            //owner launch this phase to open tokens claim by participants
            salePhase = Phases.SaleCompleted;
            emit newPhase(Phases.SaleCompleted);
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
        require(salePhase == Phases.Setup, "not setup phase");
        registrationPhaseDuration = _registrationPhaseDuration;
        guaranteedPoolPhaseDuration = _guaranteedPoolPhaseDuration;
        publicPoolPhaseDuration = _publicPoolPhaseDuration;
    }

    // function allows owner to set tiers min ftg staking threshold
    function setTiersMinFTGStakings(
        uint256 _rubyMin,
        uint256 _sapphireMin,
        uint256 _emeraldMin,
        uint256 _diamondMin
    ) public onlyOwner {
        require(salePhase == Phases.Setup, "not setup phase");
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
        require(salePhase == Phases.Setup, "not setup phase");
        require(
            _sapphireAllocationFactor > 1 &&
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
        require(
            participants[msg.sender].whitelisted == false,
            "already registered"
        );
        //TODO  requirement that KYC has been done in the frontend
        // requirement that caller is eligible
        Tiers tier = checkTierEligibility(msg.sender);
        require(tier != Tiers.NONE, "Not enough locked Staking");
        // add participant to tiersNbOFParticipants
        tiersNbOFParticipants[tier]++;
        // add participant and set whitelisted to true
        participants[msg.sender] = Participant(0, 0, true, tier);
        emit newParticipant(msg.sender, tier);
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
        // max number of tokens that ruby participant can buy
        maxNbTokensPerPartRuby = PRBMath.mulDiv(1, totalTokensToSell, sumFNP);
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
        NbOfParticipants =
            tiersNbOFParticipants[Tiers.RUBY] +
            tiersNbOFParticipants[Tiers.SAPPHIRE] +
            tiersNbOFParticipants[Tiers.EMERALD] +
            tiersNbOFParticipants[Tiers.DIAMOND];
        //remaining tokens after Guaranteed Pool
        publicPoolTokensAtPPStart = totalTokensToSell - tokensSold;
        // max tokens a participant can buy regardless his/her tier at the start of Public Pool
        // this number will then increase exponentially till end of the sale
        maxNbTokensPerPartAtPPStart = PRBMath.mulDiv(
            1,
            publicPoolTokensAtPPStart,
            NbOfParticipants
        );
    }

    //function to buy tokens during Pool Phases, buyTokenAmount in tokenWei
    function buytoken(uint256 buyTokenAmount) public {
        //verifies that participants has been KYCed
        require(participants[msg.sender].whitelisted, "not in whitelist");
        Tiers tier = participants[msg.sender].participantTier;
        require(
            salePhase == Phases.GuaranteedPool ||
                salePhase == Phases.PublicPool,
            "not open for buying"
        );
        //Guaranteed Pool Phase
        if (salePhase == Phases.GuaranteedPool) {
            //Verifies that phase is not over
            require(
                block.timestamp <
                    guaranteedPoolPhaseStart + guaranteedPoolPhaseDuration,
                "Guaranteed Pool Phase ended"
            );
            //require participant is buying less than entitled to
            require(
                participants[msg.sender].tokensBalanceGP + buyTokenAmount <=
                    maxNbTokensPerPartRuby * tiersTokensAllocationFactor[tier],
                "Maximum allowed number of tokens exceeded"
            );
            uint256 investedAmount = PRBMath.mulDiv(
                buyTokenAmount,
                tokenPrice,
                10**18
            );
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
            ntt.issue(msg.sender, buyTokenAmount);
            emit newPurchase(msg.sender, buyTokenAmount, Phases.GuaranteedPool);
            if (investmentRaised >= totalToRaise) {
                // Sale is completed and participants can claim their tokens
                salePhase = Phases.SaleCompleted;
                emit newPhase(Phases.SaleCompleted);
            }
            // Public Pool Phase
        } else if (salePhase == Phases.PublicPool) {
            //verifies that phase is not over
            require(
                block.timestamp <
                    publicPoolPhaseStart + publicPoolPhaseDuration,
                "Public Pool Phase ended"
            );
            //require that participant is buying less than entitled to:
            //the maximum of purchaseable number of tokens by a participant is a
            //linear function of time. No limit for the purchaseable number of
            //tokens after 3/4 of the public pool phase has passed
            //uint256 maxNbTokensPerPartAtPP = updateMaxNbTokensPerPartAtPP();
            uint256 publicPoolTokens = totalTokensToSell - tokensSold;
            uint256 maxNbTokensPerPartAtPP;
            if (
                4 * (block.timestamp - publicPoolPhaseStart) <
                3 * publicPoolPhaseDuration
            ) {
                maxNbTokensPerPartAtPP =
                    maxNbTokensPerPartAtPPStart +
                    PRBMath.mulDiv(
                        (block.timestamp - publicPoolPhaseStart),
                        4 * (publicPoolTokens - maxNbTokensPerPartAtPPStart),
                        3 * publicPoolPhaseDuration
                    );
            } else {
                maxNbTokensPerPartAtPP = publicPoolTokens;
            }
            require(
                participants[msg.sender].tokensBalancePP + buyTokenAmount <=
                    maxNbTokensPerPartAtPP,
                "Maximum allowed number of tokens exceeded"
            );
            uint256 investedAmount = PRBMath.mulDiv(
                buyTokenAmount,
                tokenPrice,
                10**18
            );
            //purchase takes place
            IERC20(investToken).transferFrom(
                msg.sender,
                address(this),
                investedAmount
            );
            // balances are updated
            tokensSold += buyTokenAmount;
            investmentRaised += investedAmount;
            participants[msg.sender].tokensBalancePP += buyTokenAmount;
            ntt.issue(msg.sender, buyTokenAmount);
            emit newPurchase(msg.sender, buyTokenAmount, Phases.PublicPool);

            if (investmentRaised >= totalToRaise) {
                // Sale is completed and participants can claim their tokens
                salePhase = Phases.SaleCompleted;
                emit newPhase(Phases.SaleCompleted);
            }
        }
    }

    //function for testing purpose
    function updateMaxNbTokensPerPartAtPP()
        public
        returns (uint256 maxNbTokensPerPartAtPP)
    {
        uint256 publicPoolTokens = totalTokensToSell - tokensSold;
        if (
            4 * (block.timestamp - publicPoolPhaseStart) <
            3 * publicPoolPhaseDuration
        ) {
            maxNbTokensPerPartAtPP =
                maxNbTokensPerPartAtPPStart +
                PRBMath.mulDiv(
                    (block.timestamp - publicPoolPhaseStart),
                    4 * (publicPoolTokens - maxNbTokensPerPartAtPPStart),
                    3 * publicPoolPhaseDuration
                );
        } else {
            maxNbTokensPerPartAtPP = publicPoolTokens;
        }
    }

    //********************* Helpers functions *********************/

    function getTiersTokensAllocationFactor(Tiers _tier)
        public
        view
        returns (uint256)
    {
        return tiersTokensAllocationFactor[_tier];
    }

    function getTiersNbOFParticipants(Tiers _tier)
        public
        view
        returns (uint256)
    {
        return tiersNbOFParticipants[_tier];
    }

    function getParticipantInfo(address _participant)
        public
        view
        returns (Participant memory)
    {
        return participants[_participant];
    }

    //********************* Admin functions *********************/

    function withdrawRaisedAssets() public onlyOwner {
        uint256 bal = IERC20(investToken).balanceOf(address(this));
        IERC20(investToken).transfer(msg.sender, bal);
    }

    function recoverAssets(address _token) public onlyOwner {
        uint256 bal = IERC20(_token).balanceOf(address(this));
        IERC20(_token).transfer(msg.sender, bal);
    }
}
