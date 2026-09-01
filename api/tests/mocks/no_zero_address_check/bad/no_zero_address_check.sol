pragma solidity ^0.8.20;

contract NoZeroAddressCheckBad {
    address public recipient;

    event RecipientUpdated(address indexed newRecipient);

    // Stores the recipient unchecked, so fees can be routed to address(0).
    function setRecipient(address newRecipient) external {
        recipient = newRecipient;
        emit RecipientUpdated(newRecipient);
    }
}
