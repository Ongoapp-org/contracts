// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;
import "OpenZeppelin/openzeppelin-contracts@4.1.0/contracts/token/ERC20/IERC20.sol";
import "./OwnableBase.sol";
import "./NTT.sol";

contract Redeemer is OwnableBase {
    NTT public ntt;
    address public saleToken;

    constructor(address _ntt, address _saleToken) {
        ntt = NTT(_ntt);
        saleToken = _saleToken;
    }

    //redeem all of the eligible launch token 1:1
    function claim() public {
        //require(salePhase == Phases.SaleCompleted, "sale not completed yet");
        uint256 redeemableAmount = ntt.balanceOf(msg.sender);
        ntt.redeem(msg.sender, redeemableAmount);

        IERC20(saleToken).transfer(msg.sender, redeemableAmount);
    }

    // Function for owner to deposit tokens
    function depositSaleTokens(uint256 amount) public onlyOwner {
        IERC20(saleToken).transferFrom(msg.sender, address(this), amount);
    }

    function withdrawLeftOverTokens() public onlyOwner {
        uint256 bal = IERC20(saleToken).balanceOf(address(this));
        IERC20(saleToken).transfer(msg.sender, bal);
    }

    function recoverAssets(address _token) public onlyOwner {
        uint256 bal = IERC20(_token).balanceOf(address(this));
        IERC20(_token).transfer(msg.sender, bal);
    }

    // function withdrawLeftOverTokens() public onlyOwner {
    //     //Should add requirement to avoid owner able to withdraw tokens before participants claimed
    //     //adding a claim Phase with duration could do it
    //     require(salePhase == Phases.SaleCompleted, "Sale not completed");
    //     uint256 bal = IERC20(saleToken).balanceOf(address(this));
    //     IERC20(saleToken).transfer(msg.sender, bal);
    // }
}
