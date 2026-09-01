pragma solidity ^0.8.20;

/// @notice Minimal ETH vault.
contract Vault {
    mapping(address => uint256) public balanceOf;

    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status = _NOT_ENTERED;

    modifier nonReentrant() {
        require(_status != _ENTERED, "reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }

    function deposit() external payable {
        balanceOf[msg.sender] += msg.value;
    }

    /// @dev Hands control to the caller with a value-bearing low-level call,
    ///      but the reentrancy guard blocks any re-entry.
    function withdraw(uint256 amount) external nonReentrant {
        require(balanceOf[msg.sender] >= amount, "insufficient balance");
        balanceOf[msg.sender] -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "eth transfer failed");
    }
}
