pragma solidity ^0.8.0;

contract UnprotectedConfigurationSettersGood {
    uint256 public fee;
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setFee(uint256 _fee) public onlyOwner {
        fee = _fee;
    }
}
