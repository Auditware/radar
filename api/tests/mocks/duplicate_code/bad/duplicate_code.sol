// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Vault {
    mapping(address => uint256) public balancesA;
    mapping(address => uint256) public balancesB;

    // The two deposit paths are copy-pasted: any fix to one (a cap, a pause
    // check, an event) has to be remembered for the other or they drift apart.
    function depositA(uint256 amount) external {
        require(amount > 0, "zero amount");
        balancesA[msg.sender] += amount;
    }

    function depositB(uint256 amount) external {
        require(amount > 0, "zero amount");
        balancesB[msg.sender] += amount;
    }
}
