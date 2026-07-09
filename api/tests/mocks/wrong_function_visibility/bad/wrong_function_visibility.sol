pragma solidity ^0.8.0;

contract WrongFunctionVisibilityBad {
    mapping(address => uint256) public balances;

    function _processWithdrawal(address user, uint256 amount) public {
        require(balances[user] >= amount, "insufficient balance");
        balances[user] -= amount;
        payable(user).transfer(amount);
    }
}
