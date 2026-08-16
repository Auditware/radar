pragma solidity ^0.8.0;

interface IPriceFeed {
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80);
}

contract DeprecatedGood {
    IPriceFeed public feed;

    function getPrice() external view returns (int256) {
        (, int256 price, , , ) = feed.latestRoundData();
        return price;
    }
}
