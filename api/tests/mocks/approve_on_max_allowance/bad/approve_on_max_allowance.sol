// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract LiquidityRouter {
    IERC20 public immutable token;
    address public immutable pool;

    constructor(IERC20 _token, address _pool) {
        token = _token;
        pool = _pool;
    }

    // Grants the pool an unlimited allowance that is never revoked, so a pool
    // upgrade or compromise can drain every token this router ever holds.
    function fundPool(uint256 amount) external {
        require(amount > 0, "zero amount");
        token.approve(pool, type(uint256).max);
    }
}
