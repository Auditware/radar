pragma solidity ^0.8.0;

contract SelfReferencingTokenSwapBad {
    function swap(address tokenIn, address tokenOut, uint256 amount) external pure returns (uint256) {
        return amount + uint160(tokenIn) + uint160(tokenOut);
    }
}
