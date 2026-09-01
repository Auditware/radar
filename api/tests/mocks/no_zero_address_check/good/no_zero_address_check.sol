pragma solidity ^0.8.20;

contract NoZeroAddressCheckGood {
    address public recipient;

    event RecipientUpdated(address indexed newRecipient);

    // Rejects the zero address before storing the recipient.
    function setRecipient(address newRecipient) external {
        require(newRecipient != address(0), "zero address");
        recipient = newRecipient;
        emit RecipientUpdated(newRecipient);
    }
}
