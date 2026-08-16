pragma solidity ^0.8.0;

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
}

library SafeERC20 {
    function forceApprove(IERC20 token, address spender, uint256 amount) internal {}
}

contract ApproveGood {
    using SafeERC20 for IERC20;

    function setup(IERC20 token, address spender, uint256 amount) external {
        token.forceApprove(spender, amount);
    }
}
