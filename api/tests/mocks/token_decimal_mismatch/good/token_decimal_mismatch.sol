pragma solidity ^0.8.0;

contract TokenDecimalMismatchGood {
    function getPrice(uint256 usdcAmount, uint256 wethAmount) external pure returns (uint256) {
        uint256 normalizedUsdc = usdcAmount * 1000000000000;
        return normalizedUsdc * 1000000000000000000 / (wethAmount * 1000000);
    }
}
