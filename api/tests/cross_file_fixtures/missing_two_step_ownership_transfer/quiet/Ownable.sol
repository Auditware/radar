// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// The transfer half of a two-step handover. The accept half is in Guardian.sol,
// which is the whole point: judged on this file alone the rule must fire, and
// judged on the project it must not.
contract Ownable {
    address public owner;
    address public pendingOwner;

    function transferOwnership(address newOwner) public {
        require(msg.sender == owner, "not owner");
        pendingOwner = newOwner;
    }
}
