pragma solidity ^0.8.20;

contract TxOriginUsedForAuthorizationGood {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Authorizes on the immediate caller.
    function withdraw(address payable to, uint256 amount) external {
        require(msg.sender == owner, "not owner");
        to.transfer(amount);
    }
}
