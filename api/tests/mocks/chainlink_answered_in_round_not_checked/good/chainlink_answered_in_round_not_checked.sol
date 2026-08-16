pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract RoundGood {
    AggregatorV3Interface public feed;

    function getPrice() external view returns (int256) {
        (uint80 roundId, int256 price, , uint256 updatedAt, uint80 answeredInRound) = feed.latestRoundData();
        require(updatedAt > 0, "stale");
        require(answeredInRound >= roundId, "stale round");
        require(price > 0, "bad");
        return price;
    }
}
