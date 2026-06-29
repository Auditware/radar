pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract ChainlinkMinMaxCircuitBreakerGood {
    AggregatorV3Interface public oracle;
    int256 public minPrice = 1;

    constructor(AggregatorV3Interface _oracle) {
        oracle = _oracle;
    }

    function read() external view returns (int256) {
        (, int256 price, , , ) = oracle.latestRoundData();
        require(price > minPrice, "price below floor");
        return price;
    }
}
