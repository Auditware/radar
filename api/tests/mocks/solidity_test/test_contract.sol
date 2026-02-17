// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableContract {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Vulnerable: uses tx.origin for authorization
    function dangerousWithdraw(address payable recipient) external {
        require(tx.origin == owner, "Not owner");
        recipient.transfer(address(this).balance);
    }
    
    // Vulnerable: unsafe delegatecall
    function unsafeDelegateCall(address target, bytes memory data) external {
        require(msg.sender == owner, "Not owner");
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegatecall failed");
    }
    
    receive() external payable {}
}
