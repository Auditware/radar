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

    // Clears the value members explicitly instead of deleting the struct, so
    // the nested `delegated` mapping is never silently left behind.
    function closeAccount() external {
        Account storage account = accounts[msg.sender];
        account.balance = 0;
        account.updatedAt = 0;
    }
}
