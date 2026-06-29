pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract StaleChainlinkPriceBad {
    AggregatorV3Interface public oracle;

    constructor(AggregatorV3Interface _oracle) {
        oracle = _oracle;
    }

    function read() external view returns (int256) {
        (, int256 price, , uint256 updatedAt, ) = oracle.latestRoundData();
        require(price > 0, "bad price");
        updatedAt;
        return price;
    }
}
