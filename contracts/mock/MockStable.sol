// contracts/GLDToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8;

import "OpenZeppelin/openzeppelin-contracts@4.3.0/contracts/token/ERC20/ERC20.sol";

contract MockStable is ERC20 {
    constructor(uint256 init_supply) ERC20("Mock Stable", "USDTF") {
        _mint(msg.sender, init_supply);
    }
}
