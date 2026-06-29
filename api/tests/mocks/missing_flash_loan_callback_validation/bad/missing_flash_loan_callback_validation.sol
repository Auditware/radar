pragma solidity ^0.8.0;

contract MissingFlashLoanCallbackValidationBad {
    uint256 public lastAmount;

    function onFlashLoan(address, address, uint256 amount, uint256, bytes calldata) external returns (bytes32) {
        lastAmount = amount;
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
}
