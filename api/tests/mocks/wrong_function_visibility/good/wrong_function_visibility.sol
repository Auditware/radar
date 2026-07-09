pragma solidity ^0.8.0;

contract WrongFunctionVisibilityGood {
    mapping(address => uint256) public balances;

    function withdraw(address user, uint256 amount) external {
        _processWithdrawal(user, amount);
    }

    function _processWithdrawal(address user, uint256 amount) internal {
        require(balances[user] >= amount, "insufficient balance");
        balances[user] -= amount;
        payable(user).transfer(amount);
    }
}
