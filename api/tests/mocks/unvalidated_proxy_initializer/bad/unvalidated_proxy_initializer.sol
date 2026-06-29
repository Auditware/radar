pragma solidity ^0.8.0;

contract UnvalidatedProxyInitializerBad {
    address public owner;

    function initialize(address _owner) public {
        owner = _owner;
    }
}
