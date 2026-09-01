// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Escrow {
    struct Account {
        uint256 balance;
        uint256 updatedAt;
        mapping(address => uint256) delegated;
    }

    mapping(address => Account) private accounts;

    function delegate(address to, uint256 amount) external {
        accounts[msg.sender].delegated[to] = amount;
    }

    // `delete` skips the nested `delegated` mapping, so every delegation
    // survives the close and is still live if the account is reopened.
    function closeAccount() external {
        delete accounts[msg.sender];
    }
}
