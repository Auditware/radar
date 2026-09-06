// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// The accept half, deliberately in its own file.
contract Guardian {
    address public owner;
    address public pendingOwner;

    function acceptOwnership() public {
        require(msg.sender == pendingOwner, "not pending owner");
        owner = pendingOwner;
    }
}
