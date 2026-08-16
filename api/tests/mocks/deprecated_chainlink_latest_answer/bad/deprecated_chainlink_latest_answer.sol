pragma solidity ^0.8.0;

interface IPriceFeed {
    function latestAnswer() external view returns (int256);
}

contract DeprecatedBad {
    IPriceFeed public feed;

    function getPrice() external view returns (int256) {
        return feed.latestAnswer();
    }
}
