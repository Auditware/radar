pragma solidity ^0.8.20;

/// @notice Minimal ETH vault.
contract Vault {
    mapping(address => uint256) public balanceOf;

    function deposit() external payable {
        balanceOf[msg.sender] += msg.value;
    }

    /// @dev Hands control to the caller with a value-bearing low-level call and
    ///      is not protected by a reentrancy guard.
    function withdraw(uint256 amount) external {
        require(balanceOf[msg.sender] >= amount, "insufficient balance");
        balanceOf[msg.sender] -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "eth transfer failed");
    }
}
