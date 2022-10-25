// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

//https://github.com/avalaunch-app/xava-protocol/blob/master/contracts/sales/AvalaunchSale.sol

//is Initializable
contract FTGSale {

    struct Sale {
        // Token being sold
        IERC20 token;
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
    }
}