pragma solidity ^0.8.0;

contract HardcodedExternalDependencyAddressBad {
    address constant ORACLE = 0x0000000000000000000000000000000000000001;

    function readOracle() external pure returns (address) {
        return ORACLE;
    }
}
