pragma solidity ^0.8.20;

/// @notice Fixed-price mint with a batch helper.
contract BatchMinter {
    uint256 public constant PRICE = 0.1 ether;

    mapping(uint256 => address) public ownerOf;

    /// @dev `msg.value` is re-read on every iteration, but the caller only pays
    ///      once, so a single PRICE payment mints the whole batch.
    function mintBatch(uint256[] calldata ids) external payable {
        for (uint256 i = 0; i < ids.length; i++) {
            require(msg.value >= PRICE, "underpaid");
            ownerOf[ids[i]] = msg.sender;
        }
    }
}
