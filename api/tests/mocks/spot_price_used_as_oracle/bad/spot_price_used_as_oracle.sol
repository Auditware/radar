pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112, uint112, uint32);
}

contract SpotPriceUsedAsOracleBad {
    IUniswapV2Pair public pair;

    constructor(IUniswapV2Pair _pair) {
        pair = _pair;
    }

    function getPrice() external view returns (uint256) {
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        return uint256(reserve1) * 1e18 / uint256(reserve0);
    }
}
