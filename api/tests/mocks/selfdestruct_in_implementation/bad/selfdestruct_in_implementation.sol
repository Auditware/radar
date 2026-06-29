pragma solidity ^0.8.0;

contract SelfdestructInImplementationBad {
    address public owner;
    address public implementation;

    constructor(address _owner) {
        owner = _owner;
    }

    function upgradeTo(address newImplementation) external {
        require(msg.sender == owner, "not owner");
        implementation = newImplementation;
    }

    function destroy() external {
        require(msg.sender == owner, "not owner");
        selfdestruct(payable(owner));
    }
}
