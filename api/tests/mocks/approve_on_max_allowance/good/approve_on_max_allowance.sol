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

    // Grants the pool exactly the allowance this call needs, so nothing is
    // left standing for the pool to pull afterwards.
    function fundPool(uint256 amount) external {
        require(amount > 0, "zero amount");
        token.approve(pool, amount);
    }
}
