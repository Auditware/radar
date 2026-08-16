pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract L2PriceConsumerBad {
    AggregatorV3Interface public priceFeed;

    function getPrice() external view returns (int256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        require(price > 0, "bad price");
        return price;
    }
}
