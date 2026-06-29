pragma solidity ^0.8.0;

interface IUniswapV3PoolObserve {
    function observe(uint32[] calldata secondsAgos) external view returns (int56[] memory tickCumulatives, uint160[] memory secondsPerLiquidityCumulativeX128s);
}

contract TWAPWindowTooSmallBad {
    IUniswapV3PoolObserve public pool;

    constructor(IUniswapV3PoolObserve _pool) {
        pool = _pool;
    }

    function consult() external view returns (int56[] memory) {
        uint32[] memory secondsAgo = new uint32[](2);
        secondsAgo[0] = 300;
        (int56[] memory tickCumulatives, ) = pool.observe(secondsAgo);
        return tickCumulatives;
    }
}
