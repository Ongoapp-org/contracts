// contracts/GLDToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8;

import "OpenZeppelin/openzeppelin-contracts@4.3.0/contracts/token/ERC20/ERC20.sol";

contract FTGToken is ERC20 {
    constructor(uint init_supply) ERC20("FTGToken", "FTG") {
        _mint(msg.sender, init_supply);
    }
}