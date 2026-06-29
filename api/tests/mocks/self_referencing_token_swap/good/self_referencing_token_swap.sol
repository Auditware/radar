pragma solidity ^0.8.0;

contract SelfReferencingTokenSwapGood {
    function swap(address tokenIn, address tokenOut, uint256 amount) external pure returns (uint256) {
        require(tokenIn != tokenOut, "same token");
        return amount + uint160(tokenIn) + uint160(tokenOut);
    }
}
