pragma solidity ^0.8.0;

contract TokenDecimalMismatchBad {
    function getPrice(uint256 usdcAmount, uint256 wethAmount) external pure returns (uint256) {
        return usdcAmount * 1000000000000000000 / (wethAmount * 1000000);
    }

    function getQuote(uint256 usdcAmount, uint256 wethAmount) external pure returns (uint256) {
        return usdcAmount * (10 ** 18) / (wethAmount * (10 ** 6));
    }
}
