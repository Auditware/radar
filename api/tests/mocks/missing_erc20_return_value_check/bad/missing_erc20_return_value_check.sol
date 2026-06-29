pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
}

contract MissingERC20ReturnValueCheckBad {
    IERC20 public token;

    constructor(IERC20 _token) {
        token = _token;
    }

    function payout(address recipient, uint256 amount) external {
        token.transfer(recipient, amount);
    }
}
