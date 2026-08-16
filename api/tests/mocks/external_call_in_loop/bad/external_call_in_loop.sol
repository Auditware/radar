pragma solidity ^0.8.0;

contract PayoutBad {
    address[] public recipients;

    function payout() external {
        for (uint256 i = 0; i < recipients.length; i++) {
            payable(recipients[i]).transfer(1 ether);
        }
    }
}
