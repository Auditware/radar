pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract L2PriceConsumerGood {
    AggregatorV3Interface public priceFeed;
    AggregatorV3Interface public sequencerUptimeFeed;

    function getPrice() external view returns (int256) {
        (, int256 up, uint256 startedAt, , ) = sequencerUptimeFeed.latestRoundData();
        require(up == 0, "sequencer down");
        require(block.timestamp - startedAt > 3600, "grace period");
        (, int256 price, , , ) = priceFeed.latestRoundData();
        require(price > 0, "bad price");
        return price;
    }
}
