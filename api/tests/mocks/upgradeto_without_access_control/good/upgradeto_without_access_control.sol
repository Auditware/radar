pragma solidity ^0.8.0;

contract UpgradeToWithoutAccessControlGood {
    address public implementation;
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function upgradeTo(address newImpl) public onlyOwner {
        implementation = newImpl;
    }
}
