pragma solidity ^0.8.0;

contract VaultGood {
    bool private initialized;
    address public owner;

    modifier initializer() {
        require(!initialized, "already initialized");
        initialized = true;
        _;
    }

    constructor() {
        _disableInitializers();
    }

    function initialize(address _owner) external initializer {
        owner = _owner;
    }

    function _disableInitializers() internal {
        initialized = true;
    }
}
