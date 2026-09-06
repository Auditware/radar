// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// One-step transfer, and nothing anywhere in the project completes it.
contract Ownable {
    address public owner;

    function transferOwnership(address newOwner) public {
        require(msg.sender == owner, "not owner");
        owner = newOwner;
    }
}
