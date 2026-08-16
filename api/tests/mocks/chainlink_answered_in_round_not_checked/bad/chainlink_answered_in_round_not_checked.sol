pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract RoundBad {
    AggregatorV3Interface public feed;

    function getPrice() external view returns (int256) {
        (uint80 roundId, int256 price, , uint256 updatedAt, ) = feed.latestRoundData();
        require(updatedAt > 0, "stale");
        require(price > 0, "bad");
        roundId;
        return price;
    }
}
