pragma solidity ^0.8.0;

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

contract ApproveBad {
    function setup(IERC20 token, address spender, uint256 amount) external {
        token.approve(spender, amount);
    }
}
