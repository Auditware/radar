pragma solidity ^0.8.20;

/// @notice Fixed-price mint with a batch helper.
contract BatchMinter {
    uint256 public constant PRICE = 0.1 ether;

    mapping(uint256 => address) public ownerOf;

    /// @dev `msg.value` is checked once against the total cost of the batch
    ///      before the loop, so it cannot be counted more than once.
    function mintBatch(uint256[] calldata ids) external payable {
        require(msg.value >= PRICE * ids.length, "underpaid");
        for (uint256 i = 0; i < ids.length; i++) {
            ownerOf[ids[i]] = msg.sender;
        }
    }
}
