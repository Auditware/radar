pragma solidity ^0.8.0;

contract ETHSendOrTransferUsageBad {
    function pay(address recipient, uint256 amount) external {
        payable(recipient).transfer(amount);
    }
}
