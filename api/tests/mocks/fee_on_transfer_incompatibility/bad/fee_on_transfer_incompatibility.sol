pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract FeeOnTransferIncompatibilityBad {
    IERC20 public token;
    mapping(address => uint256) public balances;

    constructor(IERC20 _token) {
        token = _token;
    }

    function deposit(address from, uint256 amount) external {
        token.transferFrom(from, address(this), amount);
        balances[from] += amount;
    }
}
