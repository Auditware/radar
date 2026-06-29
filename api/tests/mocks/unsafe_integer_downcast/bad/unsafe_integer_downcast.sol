pragma solidity ^0.8.0;

contract UnsafeIntegerDowncastBad {
    function castValue(uint256 largeValue) external pure returns (uint128) {
        uint128 x = uint128(largeValue);
        return x;
    }
}
