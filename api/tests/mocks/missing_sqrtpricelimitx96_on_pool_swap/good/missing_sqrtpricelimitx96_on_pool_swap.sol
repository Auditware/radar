pragma solidity ^0.8.0;

interface IUniswapV3Pool {
    function swap(address recipient, bool zeroForOne, int256 amountSpecified, uint160 sqrtPriceLimitX96, bytes calldata data) external returns (int256 amount0, int256 amount1);
}

contract MissingSqrtPriceLimitX96OnPoolSwapGood {
    IUniswapV3Pool public pool;

    constructor(IUniswapV3Pool _pool) {
        pool = _pool;
    }

    function swap(address recipient, bool zeroForOne, int256 amountSpecified, uint160 sqrtPriceLimitX96, bytes calldata data) external {
        pool.swap(recipient, zeroForOne, amountSpecified, sqrtPriceLimitX96, data);
    }
}
