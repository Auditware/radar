pragma solidity ^0.8.0;

contract UnvalidatedProxyInitializerGood {
    address public owner;
    bool private initialized;

    modifier initializer() {
        require(!initialized, "already initialized");
        _;
        initialized = true;
    }

    function initialize(address _owner) public initializer {
        owner = _owner;
    }
}
