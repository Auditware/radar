pragma solidity ^0.8.0;

contract UpgradeToWithoutAccessControlBad {
    address public implementation;

    function upgradeTo(address newImpl) public {
        implementation = newImpl;
    }
}
