pragma solidity ^0.8.0;

contract VaultBad {
    bool private initialized;
    address public owner;

    modifier initializer() {
        require(!initialized, "already initialized");
        initialized = true;
        _;
    }

    function initialize(address _owner) external initializer {
        owner = _owner;
    }
}
