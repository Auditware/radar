pragma solidity ^0.8.0;

contract ETHSendOrTransferUsageGood {
    function pay(address recipient, uint256 amount) external {
        (bool success, ) = payable(recipient).call{value: amount}("");
        require(success, "call failed");
    }
}
