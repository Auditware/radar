pragma solidity ^0.8.0;

contract HiddenFeeDrainGood {
    address public feeWallet;
    mapping(address => uint256) internal _balances;

    constructor(address _feeWallet) {
        feeWallet = _feeWallet;
    }

    function _transfer(address from, address to, uint256 amount) internal {
        uint256 fee = amount / 10;
        _balances[from] -= amount;
        _balances[feeWallet] += fee;
        _balances[to] += amount - fee;
    }
}
