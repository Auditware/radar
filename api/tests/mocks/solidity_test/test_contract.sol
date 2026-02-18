// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Test contract with multiple Solidity vulnerabilities

contract VulnerableContract {
    address public owner;
    uint256 public fee;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Vulnerable: unexplicit pragma (has ^)
    // Should be caught by unexplicit_pragma.yaml
    
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
    
    // Vulnerable: no require on set fee
    // Should be caught by no_require_on_set_fee.yaml
    function setFee(uint256 newFee) external {
        fee = newFee;
    }
    
    // Vulnerable: loss of precision (division before multiplication)
    function calculateReward(uint256 amount, uint256 rate) public pure returns (uint256) {
        return (amount / 100) * rate;
    }
    
    receive() external payable {}
}
