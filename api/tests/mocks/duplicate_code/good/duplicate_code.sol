// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Vault {
    mapping(address => uint256) public balancesA;
    mapping(address => uint256) public balancesB;

    // A single deposit path shared by both books, so the validation lives in
    // exactly one place and cannot drift between them.
    function deposit(bool toA, uint256 amount) external {
        require(amount > 0, "zero amount");
        if (toA) {
            balancesA[msg.sender] += amount;
        } else {
            balancesB[msg.sender] += amount;
        }
    }
}
