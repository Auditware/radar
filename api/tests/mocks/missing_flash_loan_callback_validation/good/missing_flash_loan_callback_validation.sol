pragma solidity ^0.8.0;

contract MissingFlashLoanCallbackValidationGood {
    address public lendingPool;
    uint256 public lastAmount;

    constructor(address _lendingPool) {
        lendingPool = _lendingPool;
    }

    function onFlashLoan(address, address, uint256 amount, uint256, bytes calldata) external returns (bytes32) {
        require(msg.sender == lendingPool, "invalid lender");
        lastAmount = amount;
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
}
