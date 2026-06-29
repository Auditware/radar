pragma solidity ^0.8.0;

contract MissingTwoStepOwnershipTransferBad {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function transferOwnership(address newOwner) external {
        require(msg.sender == owner, "not owner");
        owner = newOwner;
    }
}
