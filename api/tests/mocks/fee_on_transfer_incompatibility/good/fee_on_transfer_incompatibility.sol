pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract FeeOnTransferIncompatibilityGood {
    IERC20 public token;
    mapping(address => uint256) public balances;

    constructor(IERC20 _token) {
        token = _token;
    }

    function deposit(address from, uint256 amount) external {
        uint256 beforeBalance = token.balanceOf(address(this));
        token.transferFrom(from, address(this), amount);
        uint256 received = token.balanceOf(address(this)) - beforeBalance;
        balances[from] += received;
    }
}
