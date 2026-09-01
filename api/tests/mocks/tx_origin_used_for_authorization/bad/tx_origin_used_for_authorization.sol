pragma solidity ^0.8.20;

contract TxOriginUsedForAuthorizationBad {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Authorizes on tx.origin, so any contract the owner calls can withdraw.
    function withdraw(address payable to, uint256 amount) external {
        require(tx.origin == owner, "not owner");
        to.transfer(amount);
    }
}
