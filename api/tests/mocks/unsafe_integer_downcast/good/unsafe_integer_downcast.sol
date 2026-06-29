pragma solidity ^0.8.0;

contract UnsafeIntegerDowncastGood {
    function castValue(uint256 largeValue) external pure returns (uint128) {
        require(largeValue <= type(uint128).max, "value too large");
        uint128 x = uint128(largeValue);
        return x;
    }
}
