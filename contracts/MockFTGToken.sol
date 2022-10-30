// contracts/GLDToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8;

import "OpenZeppelin/openzeppelin-contracts@4.3.0/contracts/token/ERC20/ERC20.sol";

contract MockFTGToken is ERC20 {
    constructor(uint256 init_supply) ERC20("FTGToken", "FTG") {
        _mint(msg.sender, init_supply);
    }
}
